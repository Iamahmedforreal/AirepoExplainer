from urllib.parse import urlparse
import os
import asyncio
from github import Github
from app.services.validation import validate_github_repo_url
from app.models.users import RepoStatus, Repository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from git import Repo
from app.config.config import settings
from app.celery.task import clone_repository

# Wrap token in Github client, not raw string
github_client = Github(settings.github_api_key)



async def extract_repo_info(github_url: str):
    try:
       
        await validate_github_repo_url(github_url)

        # Step 2 — extract owner and repo name from URL
        owner, repo_name = await get_owner_and_repo(github_url)

        directory_name = os.path.join("cloned_repos", f"{owner}_{repo_name}")

        repo_metadata = github_client.get_repo(f"{owner}/{repo_name}")

        clone_repository.delay(github_url, directory_name)

        return mapMetadataToDbFields(repo_metadata, github_url)

    except Exception as error:
        raise ValueError(f"Failed to extract repo info: {error}")


async def get_owner_and_repo(github_url: str):
    try:
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("URL must contain both owner and repository name")
        return path_parts[0], path_parts[1].replace(".git", "")
    except Exception as error:
        raise ValueError(f"Invalid GitHub URL: {error}")


def mapMetadataToDbFields(metadata, github_url: str): 
    return {
        "githubUrl": github_url,                       
        "repoName": metadata.name,
        "repoOwner": metadata.owner.login,
        "defaultBranch": metadata.default_branch,
        "isPrivate": metadata.private,
        "sizeKb": metadata.size,
        "description": metadata.description,
        "language": metadata.language,
        "topics": metadata.get_topics(),
        "stars": metadata.stargazers_count,
        "license": metadata.license.spdx_id if metadata.license else None,
        "isArchived": metadata.archived,
        "repoCreatedAt": metadata.created_at,
        "repoUpdatedAt": metadata.updated_at,
    }



async def save_repo(user_id: str, metadata: dict, db: AsyncSession) -> Repository | None:
    try:
        existing = await check_existing_repo(user_id, metadata, db)
        if existing:
            return {"message": "Repository already exists", "data": existing}


        new_repo = Repository(
            id=str(uuid.uuid4()),
            userId=user_id,
            githubUrl=metadata["githubUrl"],
            repoName=metadata.get("repoName"),
            repoOwner=metadata.get("repoOwner"),
            defaultBranch=metadata.get("defaultBranch"),
            isPrivate=metadata.get("isPrivate", False),
            sizeKb=metadata.get("sizeKb"),
            description=metadata.get("description"),
            language=metadata.get("language"),
            topics=metadata.get("topics", []),
            stars=metadata.get("stars"),
            license=metadata.get("license"),
            isArchived=metadata.get("isArchived", False),
            repoCreatedAt=metadata.get("repoCreatedAt"),
            repoUpdatedAt=metadata.get("repoUpdatedAt"),
            status=RepoStatus.PENDING,
        )

        db.add(new_repo)
        await db.commit()
        await db.refresh(new_repo)
        return new_repo

    except KeyError as e:
        raise ValueError(f"Missing required field in metadata: {str(e)}")
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error while saving repo: {str(e)}")


async def check_existing_repo(user_id: str, metadata: dict, db: AsyncSession) -> Repository | None:
    github_url = metadata.get("githubUrl")
    if not github_url:
        raise ValueError("metadata must contain a 'githubUrl' key")

    query = select(Repository).where(
        Repository.userId == user_id,
        Repository.githubUrl == github_url
    )
    result = await db.execute(query)
    return result.scalars().first()