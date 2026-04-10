from ullrib.parse import parse_url
import os
from dotenv import load_dotenv
from github import Github

load_dotenv()
# This service is responsible for handling URL-related operations, such as validating GitHub repository URLs and extracting relevant information from them.
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")

async def extract_repo_info(github_url: str):
    try:
        parsed = parse_url(github_url)
        if parsed.domain != "github.com":
            raise ValueError("URL must be a GitHub repository URL")
        
        owner , repo_name = await get_owner_and_repo(github_url)

        try:
            metadata = await GITHUB_API_KEY.get_repo(f"{owner}/{repo_name}")
            return mapMetadataToDbFields(metadata)
        except Exception as error:
            raise ValueError(f"Error fetching repository information: {error}")
    except Exception as error:
        raise ValueError(f"Invalid GitHub URL: {error}")

# this function is used to extract the owner and repository name from a GitHub URL
async def get_owner_and_repo(github_url: str):
    try:
        parsed = parse_url(github_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("URL must contain both owner and repository name")
        owner = path_parts[0]
        repo_name = path_parts[1]
        return owner, repo_name
    except Exception as error:
        raise ValueError(f"Invalid GitHub URL: {error}")
    
def mapMetadataToDbFields(metadata):
    return {
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
        "repoUpdatedAt": metadata.updated_at
    }

async def save_metadata_to_db(metadata, user_id):
    pass
    
