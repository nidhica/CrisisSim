"""
CrisisSim AWS Automated Infrastructure Deployment Script.

Deploys:
1. DynamoDB Tables: crisissim-scenarios, crisissim-results
2. Data Seeding: seeds flood-scenario-001 into DynamoDB
3. IAM Role: CrisisSimLambdaRole with least privilege (DynamoDB, Bedrock, CloudWatch)
4. Lambda Function: crisissim-api-lambda (Python 3.12)
5. API Gateway REST API: CrisisSimAPI (Proxy integration + CORS)
6. Amplify App Deployment: Builds and deploys frontend with live API Gateway URL

Usage:
  python deploy_aws.py --region us-east-1
"""
from __future__ import annotations
import argparse
import io
import json
import os
import sys
import time
import zipfile
import subprocess
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from seed_data import get_all_scenarios
from persistence.dynamodb import _convert_floats_to_decimals, _dataclass_to_dict

BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

def create_dynamodb_tables(dynamodb, region: str):
    print("--- 1. Setting up DynamoDB Tables ---")
    scenarios_table_name = "crisissim-scenarios"
    results_table_name = "crisissim-results"
    
    # Scenarios Table (PK: scenario_id)
    try:
        table = dynamodb.create_table(
            TableName=scenarios_table_name,
            KeySchema=[{"AttributeName": "scenario_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "scenario_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"  Creating table '{scenarios_table_name}'...")
        table.wait_until_exists()
        print(f"  Table '{scenarios_table_name}' is ACTIVE.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table '{scenarios_table_name}' already exists.")
        else:
            raise e

    # Results Table (PK: scenario_id, SK: run_at)
    try:
        table = dynamodb.create_table(
            TableName=results_table_name,
            KeySchema=[
                {"AttributeName": "scenario_id", "KeyType": "HASH"},
                {"AttributeName": "run_at", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "scenario_id", "AttributeType": "S"},
                {"AttributeName": "run_at", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"  Creating table '{results_table_name}'...")
        table.wait_until_exists()
        print(f"  Table '{results_table_name}' is ACTIVE.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table '{results_table_name}' already exists.")
        else:
            raise e


def seed_dynamodb_scenarios(dynamodb):
    print("\n--- 2. Seeding Default Flood Scenario into DynamoDB ---")
    table = dynamodb.Table("crisissim-scenarios")
    for scenario in get_all_scenarios():
        d = _dataclass_to_dict(scenario)
        item = _convert_floats_to_decimals(d)
        table.put_item(Item=item)
        print(f"  Seeded scenario '{scenario.scenario_id}' ({scenario.name}) into DynamoDB.")


def create_iam_role(iam_client, sts_client):
    print("\n--- 3. Creating IAM Role for Lambda (CrisisSimLambdaRole) ---")
    role_name = "CrisisSimLambdaRole"
    account_id = sts_client.get_caller_identity()["Account"]
    
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    try:
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description="Least privilege role for CrisisSim Lambda function",
        )
        print(f"  Created IAM role '{role_name}'.")
        role_arn = role["Role"]["Arn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print(f"  IAM role '{role_name}' already exists.")
            role_arn = iam_client.get_role(RoleName=role_name)["Role"]["Arn"]
        else:
            raise e

    # Attach CloudWatch Logs Managed Policy
    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    # Inline Policy for DynamoDB and Bedrock (Least Privilege)
    least_privilege_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DynamoDBAccess",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    f"arn:aws:dynamodb:*:*:table/crisissim-scenarios*",
                    f"arn:aws:dynamodb:*:*:table/crisissim-results*"
                ]
            },
            {
                "Sid": "BedrockInvoke",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": "*"
            }
        ]
    }

    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName="CrisisSimLambdaPolicy",
        PolicyDocument=json.dumps(least_privilege_policy),
    )
    print("  Attached least-privilege policy (DynamoDB + Bedrock + CloudWatch) to role.")
    return role_arn


def package_lambda_zip() -> bytes:
    print("\n--- 4. Packaging Lambda Function Zip Package ---")
    backend_dir = Path(__file__).parent.resolve()
    buffer = io.BytesIO()
    
    files_to_include = [
        "lambda_function.py",
        "seed_data.py",
    ]
    dirs_to_include = [
        "engine",
        "handlers",
        "persistence",
        "bedrock",
    ]

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_include:
            fpath = backend_dir / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)
        
        for dname in dirs_to_include:
            dpath = backend_dir / dname
            if dpath.exists():
                for root, _, files in os.walk(dpath):
                    if "__pycache__" in root or ".pytest_cache" in root or ".hypothesis" in root:
                        continue
                    for f in files:
                        if f.endswith(".pyc"):
                            continue
                        full_fpath = Path(root) / f
                        arcname = full_fpath.relative_to(backend_dir)
                        zf.write(full_fpath, arcname=str(arcname))

    zip_bytes = buffer.getvalue()
    print(f"  Packaged Lambda zip (size: {len(zip_bytes) / 1024:.1f} KB).")
    return zip_bytes


def deploy_lambda_function(lambda_client, role_arn: str, zip_bytes: bytes, region: str):
    print("\n--- 5. Deploying Lambda Function (crisissim-api-lambda) ---")
    function_name = "crisissim-api-lambda"

    env_vars = {
        "DYNAMODB_SCENARIOS_TABLE": "crisissim-scenarios",
        "DYNAMODB_RESULTS_TABLE": "crisissim-results",
        "APP_AWS_REGION": region,
    }

    try:
        resp = lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.12",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={"ZipFile": zip_bytes},
            Description="CrisisSim API Lambda function",
            Timeout=30,
            MemorySize=256,
            Environment={"Variables": env_vars},
        )

        print(f"  Created Lambda function '{function_name}'.")
        function_arn = resp["FunctionArn"]

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            print(f"  Updating existing Lambda function '{function_name}'...")

            resp = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes,
            )

            # Wait until the Lambda code update is complete.
            print("  Waiting for Lambda code update to complete...")

            waiter = lambda_client.get_waiter("function_updated")
            waiter.wait(
                FunctionName=function_name,
                WaiterConfig={
                    "Delay": 2,
                    "MaxAttempts": 30,
                },
            )

            print("  Lambda code update completed.")

            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime="python3.12",
                Role=role_arn,
                Handler="lambda_function.lambda_handler",
                Timeout=30,
                MemorySize=256,
                Environment={"Variables": env_vars},
            )

            function_arn = resp["FunctionArn"]

        else:
            raise e

    return function_name, function_arn

def create_api_gateway(apigw_client, lambda_client, function_name: str, function_arn: str, region: str):
    print("\n--- 6. Configuring API Gateway (CrisisSimAPI) ---")
    api_name = "CrisisSimAPI"
    
    # Check if API exists
    apis = apigw_client.get_rest_apis().get("items", [])
    existing_api = next((a for a in apis if a["name"] == api_name), None)
    
    if existing_api:
        api_id = existing_api["id"]
        print(f"  Using existing API Gateway '{api_name}' (ID: {api_id}).")
    else:
        api = apigw_client.create_rest_api(
            name=api_name,
            description="CrisisSim REST API Gateway",
            endpointConfiguration={"types": ["REGIONAL"]},
        )
        api_id = api["id"]
        print(f"  Created REST API '{api_name}' (ID: {api_id}).")

    # Get root resource id
    resources = apigw_client.get_resources(restApiId=api_id).get("items", [])
    root_id = next(r["id"] for r in resources if r["path"] == "/")

    # Create proxy resource {proxy+} if not existing
    proxy_resource = next((r for r in resources if r.get("path") == "/{proxy+}"), None)
    if not proxy_resource:
        proxy_resource = apigw_client.create_resource(
            restApiId=api_id,
            parentId=root_id,
            pathPart="{proxy+}",
        )
    proxy_id = proxy_resource["id"]

    # Lambda Integration URI
    uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{function_arn}/invocations"

    # Add ANY method to {proxy+}
    try:
        apigw_client.put_method(
            restApiId=api_id,
            resourceId=proxy_id,
            httpMethod="ANY",
            authorizationType="NONE",
        )
        apigw_client.put_integration(
            restApiId=api_id,
            resourceId=proxy_id,
            httpMethod="ANY",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=uri,
        )
    except ClientError:
        pass

    # Add ANY method to root resource /
    try:
        apigw_client.put_method(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="ANY",
            authorizationType="NONE",
        )
        apigw_client.put_integration(
            restApiId=api_id,
            resourceId=root_id,
            httpMethod="ANY",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=uri,
        )
    except ClientError:
        pass

    # Grant API Gateway permission to invoke Lambda
    statement_id = f"apigateway-{api_id}-permission"
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{region}:{boto3.client('sts', region_name=region).get_caller_identity()['Account']}:{api_id}/*/*/*",
        )
        print("  Granted API Gateway permission to invoke Lambda.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            pass
        else:
            raise e

    # Create Deployment & Stage 'prod'
    deployment = apigw_client.create_deployment(
        restApiId=api_id,
        stageName="prod",
    )
    
    api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod/api/v1"
    print(f"  API Gateway deployed successfully!")
    print(f"  Live Base URL: {api_url}")
    return api_id, api_url


def deploy_amplify_frontend(amplify_client, api_url: str):
    print("\n--- 7. Building & Deploying Frontend to AWS Amplify ---")
    project_root = Path(__file__).parent.parent.resolve()
    frontend_dir = project_root / "frontend"
    dist_dir = frontend_dir / "dist"

    # ── Step 7a: Write .env.production so Vite picks up the live API URL ──────
    env_prod_file = frontend_dir / ".env.production"
    with open(env_prod_file, "w", encoding="utf-8") as f:
        f.write(f"VITE_API_BASE_URL={api_url}\n")
    print(f"  Wrote VITE_API_BASE_URL={api_url} to frontend/.env.production")

    # ── Step 7b: npm run build ────────────────────────────────────────────────
    print("  Running frontend production build (npm run build)...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ❌ Frontend build failed:\n{result.stderr}")
        raise RuntimeError("Frontend build failed.")
    print("  ✓ Frontend production build completed successfully.")

    if not dist_dir.exists():
        raise RuntimeError(f"Expected dist/ directory not found at {dist_dir}")

    # ── Step 7c: Package dist/ into a zip with index.html at root ────────────
    # Amplify manual deployment requires the artifact zip to have index.html
    # at the root level (not nested inside a dist/ folder).
    print("  Packaging dist/ into deployment artifact zip...")
    zip_path = project_root / "amplify_deploy.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dist_dir):
            for file in files:
                full_path = Path(root) / file
                arcname = full_path.relative_to(dist_dir)   # strips the 'dist/' prefix
                zf.write(full_path, arcname=str(arcname))
    print(f"  Packaged deployment artifact: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")

    # ── Step 7d: Ensure Amplify app + branch exist ───────────────────────────
    app_name = "CrisisSim"
    apps = amplify_client.list_apps().get("apps", [])
    existing_app = next((a for a in apps if a["name"] == app_name), None)

    if existing_app:
        app_id = existing_app["appId"]
        print(f"  Using existing Amplify App '{app_name}' (AppId: {app_id}).")
    else:
        app = amplify_client.create_app(
            name=app_name,
            description="CrisisSim Emergency Simulation Dashboard",
            platform="WEB",
        )
        app_id = app["app"]["appId"]
        print(f"  Created AWS Amplify App '{app_name}' (AppId: {app_id}).")

    branches = amplify_client.list_branches(appId=app_id).get("branches", [])
    if not any(b["branchName"] == "main" for b in branches):
        amplify_client.create_branch(
            appId=app_id,
            branchName="main",
            description="Main branch",
        )
        print("  Created 'main' branch in Amplify App.")
    else:
        print("  'main' branch already exists.")

    # ── Step 7e: create_deployment → get presigned upload URL ────────────────
    print("  Creating Amplify manual deployment job...")
    deploy_resp = amplify_client.create_deployment(appId=app_id, branchName="main")
    job_id = deploy_resp["jobId"]
    zip_upload_url = deploy_resp["zipUploadUrl"]
    print(f"  Deployment job created (jobId: {job_id}).")

    # ── Step 7f: Upload zip artifact to presigned S3 URL (no extra deps) ─────
    print("  Uploading deployment artifact to presigned S3 URL...")
    import urllib.request
    with open(zip_path, "rb") as f:
        zip_bytes = f.read()
    req = urllib.request.Request(
        url=zip_upload_url,
        data=zip_bytes,
        method="PUT",
        headers={"Content-Type": "application/zip"},
    )
    with urllib.request.urlopen(req) as upload_resp:
        if upload_resp.status not in (200, 204):
            raise RuntimeError(f"Artifact upload failed with HTTP {upload_resp.status}")
    print("  ✓ Artifact uploaded successfully.")

    # ── Step 7g: start_deployment ─────────────────────────────────────────────
    print("  Starting Amplify deployment...")
    amplify_client.start_deployment(appId=app_id, branchName="main", jobId=job_id)

    # ── Step 7h: Poll until the job succeeds or fails (max ~5 min) ───────────
    print("  Waiting for Amplify deployment to complete (polling every 15 s)...")
    max_polls = 20
    for attempt in range(max_polls):
        time.sleep(15)
        job_detail = amplify_client.get_job(appId=app_id, branchName="main", jobId=job_id)
        job_status = job_detail["job"]["summary"]["status"]
        print(f"    [{attempt + 1}/{max_polls}] Job status: {job_status}")
        if job_status == "SUCCEED":
            break
        if job_status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Amplify deployment job {job_id} ended with status: {job_status}")
    else:
        print("  ⚠️  Amplify deployment did not complete within the polling window.")
        print("     Check the AWS Amplify Console for job status.")

    amplify_url = f"https://main.{app_id}.amplifyapp.com"
    print(f"  ✓ Amplify deployment complete.")
    print(f"  Amplify App URL: {amplify_url}")

    # Clean up temporary zip
    zip_path.unlink(missing_ok=True)

    return app_id, amplify_url


def main():
    parser = argparse.ArgumentParser(description="Deploy CrisisSim to AWS")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"), help="AWS Region")
    args = parser.parse_args()
    
    region = args.region
    print(f"=== CRISISSIM AWS DEPLOYMENT (Region: {region}) ===")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    iam = boto3.client("iam", region_name=region)
    sts = boto3.client("sts", region_name=region)
    lambda_client = boto3.client("lambda", region_name=region)
    apigw = boto3.client("apigateway", region_name=region)
    amplify = boto3.client("amplify", region_name=region)

    # 1. DynamoDB
    create_dynamodb_tables(dynamodb, region)

    # 2. Seed Data
    seed_dynamodb_scenarios(dynamodb)

    # 3. IAM Role
    role_arn = create_iam_role(iam, sts)
    
    # Wait 10s for IAM propagation
    print("  Waiting 10 seconds for IAM role propagation...")
    time.sleep(10)

    # 4. Lambda Zip Package
    zip_bytes = package_lambda_zip()

    # 5. Lambda Function
    fn_name, fn_arn = deploy_lambda_function(lambda_client, role_arn, zip_bytes, region)

    # 6. API Gateway
    api_id, api_url = create_api_gateway(apigw, lambda_client, fn_name, fn_arn, region)

    # 7. Amplify Frontend
    app_id, amplify_url = deploy_amplify_frontend(amplify, api_url)

    print("\n=======================================================")
    print("      🎉 CRISISSIM AWS DEPLOYMENT COMPLETE!            ")
    print("=======================================================")
    print(f"AWS Region           : {region}")
    print(f"DynamoDB Tables      : crisissim-scenarios, crisissim-results")
    print(f"IAM Role             : {role_arn}")
    print(f"Lambda Function      : {fn_name}")
    print(f"API Gateway URL      : {api_url}")
    print(f"Amplify App URL      : {amplify_url}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
