#!/usr/bin/env python3
"""
Script to build AWS Lambda layer for RCA Bot dependencies
"""

import os
import subprocess
import shutil
import zipfile

def create_lambda_layer():
    """Create Lambda layer with all dependencies"""
    
    # Create layer directory structure
    layer_dir = "layer/python"
    os.makedirs(layer_dir, exist_ok=True)
    
    # Install dependencies for Lambda
    dependencies = [
        "langchain",
        "langchain-community", 
        "langchain-core",
        "faiss-cpu",
        "sentence-transformers",
        "fastapi",
        "python-docx",
        "docx2txt",
        "pydantic",
        "requests",
        "boto3",
        "aws-lambda-powertools"
    ]
    
    print("Installing Lambda dependencies...")
    
    # Install dependencies to layer directory
    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.run([
            "pip", "install", 
            "--target", layer_dir,
            "--platform", "manylinux2014_x86_64",
            "--only-binary=:all:",
            dep
        ], check=True)
    
    # Create zip file
    print("Creating layer zip file...")
    with zipfile.ZipFile("layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("layer"):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, "layer")
                zipf.write(file_path, arc_path)
    
    print("Layer created successfully: layer.zip")
    
    # Clean up
    shutil.rmtree("layer")
    
    return "layer.zip"

if __name__ == "__main__":
    create_lambda_layer()
