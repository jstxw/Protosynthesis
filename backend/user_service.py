from typing import Optional, List, Dict
from database import get_collection
from datetime import datetime
import uuid

class UserService:
    """
    Service layer for managing users, projects, and workflows in MongoDB.
    Handles the nested structure: User -> Projects -> Workflows
    """

    @staticmethod
    def create_user(supabase_user_id: str, email: str) -> Dict:
        """
        Create a new user document in MongoDB when they sign up via Supabase.

        Args:
            supabase_user_id: UUID from Supabase Auth
            email: User's email address

        Returns:
            dict: The created user document
        """
        users_collection = get_collection('users')

        # Check if user already exists
        existing_user = users_collection.find_one({"supabase_user_id": supabase_user_id})
        if existing_user:
            return existing_user

        # Create new user document
        user_doc = {
            "supabase_user_id": supabase_user_id,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "projects": []
        }

        users_collection.insert_one(user_doc)
        return user_doc

    @staticmethod
    def get_user(supabase_user_id: str) -> Optional[Dict]:
        """
        Get user document by Supabase user ID.

        Args:
            supabase_user_id: UUID from Supabase Auth

        Returns:
            dict or None: User document if found
        """
        users_collection = get_collection('users')
        return users_collection.find_one({"supabase_user_id": supabase_user_id})

    @staticmethod
    def create_project(supabase_user_id: str, project_name: str) -> Dict:
        """
        Create a new project for a user.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_name: Name of the project

        Returns:
            dict: The created project object
        """
        users_collection = get_collection('users')

        project = {
            "project_id": str(uuid.uuid4()),
            "name": project_name,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "workflows": []
        }

        # Add project to user's projects array
        users_collection.update_one(
            {"supabase_user_id": supabase_user_id},
            {"$push": {"projects": project}}
        )

        return project

    @staticmethod
    def get_project(supabase_user_id: str, project_id: str) -> Optional[Dict]:
        """
        Get a specific project by ID.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID

        Returns:
            dict or None: Project object if found
        """
        users_collection = get_collection('users')

        user = users_collection.find_one(
            {"supabase_user_id": supabase_user_id},
            {"projects": {"$elemMatch": {"project_id": project_id}}}
        )

        if user and "projects" in user and len(user["projects"]) > 0:
            return user["projects"][0]
        return None

    @staticmethod
    def get_all_projects(supabase_user_id: str) -> List[Dict]:
        """
        Get all projects for a user.

        Args:
            supabase_user_id: UUID from Supabase Auth

        Returns:
            list: List of project objects
        """
        user = UserService.get_user(supabase_user_id)
        return user.get("projects", []) if user else []

    @staticmethod
    def update_project(supabase_user_id: str, project_id: str, update_data: Dict) -> bool:
        """
        Update project metadata (name, etc).

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID
            update_data: Dict with fields to update

        Returns:
            bool: True if successful
        """
        users_collection = get_collection('users')

        # Build update operations
        update_ops = {"projects.$.updated_at": datetime.utcnow().isoformat()}

        if "name" in update_data:
            update_ops["projects.$.name"] = update_data["name"]

        result = users_collection.update_one(
            {
                "supabase_user_id": supabase_user_id,
                "projects.project_id": project_id
            },
            {"$set": update_ops}
        )

        return result.modified_count > 0

    @staticmethod
    def delete_project(supabase_user_id: str, project_id: str) -> bool:
        """
        Delete a project and all its workflows.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID

        Returns:
            bool: True if successful
        """
        users_collection = get_collection('users')

        result = users_collection.update_one(
            {"supabase_user_id": supabase_user_id},
            {"$pull": {"projects": {"project_id": project_id}}}
        )

        return result.modified_count > 0

    @staticmethod
    def create_workflow(supabase_user_id: str, project_id: str, workflow_name: str, workflow_data: Optional[Dict] = None) -> Dict:
        """
        Create a new workflow within a project.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID
            workflow_name: Name of the workflow
            workflow_data: Initial workflow data (nodes, edges, etc)

        Returns:
            dict: The created workflow object
        """
        users_collection = get_collection('users')

        workflow = {
            "workflow_id": str(uuid.uuid4()),
            "name": workflow_name,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "data": workflow_data or {"nodes": [], "edges": []}
        }

        # Add workflow to the project's workflows array
        result = users_collection.update_one(
            {
                "supabase_user_id": supabase_user_id,
                "projects.project_id": project_id
            },
            {
                "$push": {"projects.$.workflows": workflow},
                "$set": {"projects.$.updated_at": datetime.utcnow().isoformat()}
            }
        )

        if result.modified_count == 0:
            raise ValueError(f"Project {project_id} not found")

        return workflow

    @staticmethod
    def get_workflow(supabase_user_id: str, project_id: str, workflow_id: str) -> Optional[Dict]:
        """
        Get a specific workflow by ID.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID
            workflow_id: Workflow UUID

        Returns:
            dict or None: Workflow object if found
        """
        users_collection = get_collection('users')

        # Use aggregation to find the specific workflow
        pipeline = [
            {"$match": {"supabase_user_id": supabase_user_id}},
            {"$unwind": "$projects"},
            {"$match": {"projects.project_id": project_id}},
            {"$unwind": "$projects.workflows"},
            {"$match": {"projects.workflows.workflow_id": workflow_id}},
            {"$project": {"workflow": "$projects.workflows", "_id": 0}}
        ]

        result = list(users_collection.aggregate(pipeline))

        if result and len(result) > 0:
            return result[0]["workflow"]
        return None

    @staticmethod
    def get_all_workflows(supabase_user_id: str, project_id: str) -> List[Dict]:
        """
        Get all workflows for a project.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID

        Returns:
            list: List of workflow objects
        """
        project = UserService.get_project(supabase_user_id, project_id)
        return project.get("workflows", []) if project else []

    @staticmethod
    def update_workflow(supabase_user_id: str, project_id: str, workflow_id: str, workflow_data: Dict) -> bool:
        """
        Update workflow data (nodes, edges, config, etc).

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID
            workflow_id: Workflow UUID
            workflow_data: New workflow data

        Returns:
            bool: True if successful
        """
        users_collection = get_collection('users')

        # First, get the user and find the workflow position
        user = users_collection.find_one({"supabase_user_id": supabase_user_id})

        if not user:
            return False

        # Find project and workflow indices
        project_idx = None
        workflow_idx = None

        for p_idx, project in enumerate(user.get("projects", [])):
            if project["project_id"] == project_id:
                project_idx = p_idx
                for w_idx, workflow in enumerate(project.get("workflows", [])):
                    if workflow["workflow_id"] == workflow_id:
                        workflow_idx = w_idx
                        break
                break

        if project_idx is None or workflow_idx is None:
            return False

        # Update the workflow
        update_ops = {
            f"projects.{project_idx}.workflows.{workflow_idx}.data": workflow_data,
            f"projects.{project_idx}.workflows.{workflow_idx}.updated_at": datetime.utcnow().isoformat(),
            f"projects.{project_idx}.updated_at": datetime.utcnow().isoformat()
        }

        result = users_collection.update_one(
            {"supabase_user_id": supabase_user_id},
            {"$set": update_ops}
        )

        return result.modified_count > 0

    @staticmethod
    def update_workflow_metadata(supabase_user_id: str, project_id: str, workflow_id: str, name: str) -> bool:
        """
        Update workflow metadata (name).

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID
            workflow_id: Workflow UUID
            name: New workflow name

        Returns:
            bool: True if successful
        """
        users_collection = get_collection('users')

        user = users_collection.find_one({"supabase_user_id": supabase_user_id})

        if not user:
            return False

        # Find indices
        project_idx = None
        workflow_idx = None

        for p_idx, project in enumerate(user.get("projects", [])):
            if project["project_id"] == project_id:
                project_idx = p_idx
                for w_idx, workflow in enumerate(project.get("workflows", [])):
                    if workflow["workflow_id"] == workflow_id:
                        workflow_idx = w_idx
                        break
                break

        if project_idx is None or workflow_idx is None:
            return False

        update_ops = {
            f"projects.{project_idx}.workflows.{workflow_idx}.name": name,
            f"projects.{project_idx}.workflows.{workflow_idx}.updated_at": datetime.utcnow().isoformat(),
        }

        result = users_collection.update_one(
            {"supabase_user_id": supabase_user_id},
            {"$set": update_ops}
        )

        return result.modified_count > 0

    @staticmethod
    def delete_workflow(supabase_user_id: str, project_id: str, workflow_id: str) -> bool:
        """
        Delete a workflow from a project.

        Args:
            supabase_user_id: UUID from Supabase Auth
            project_id: Project UUID
            workflow_id: Workflow UUID

        Returns:
            bool: True if successful
        """
        users_collection = get_collection('users')

        result = users_collection.update_one(
            {
                "supabase_user_id": supabase_user_id,
                "projects.project_id": project_id
            },
            {
                "$pull": {"projects.$.workflows": {"workflow_id": workflow_id}},
                "$set": {"projects.$.updated_at": datetime.utcnow().isoformat()}
            }
        )

        return result.modified_count > 0
