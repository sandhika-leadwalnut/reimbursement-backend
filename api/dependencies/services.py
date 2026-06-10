from fastapi import Depends
from supabase import Client
from api.dependencies.auth import get_db_client
from repositories.impl import ProfileRepository, ReimbursementRepository, AuditLogRepository
from services.auth import AuthService
from services.reimbursement import ReimbursementService
from services.storage import StorageService
from services.audit import AuditService
from services.zoho import ZohoExpenseService

def get_profile_repo(client: Client = Depends(get_db_client)) -> ProfileRepository:
    return ProfileRepository(client)

def get_reimbursement_repo(client: Client = Depends(get_db_client)) -> ReimbursementRepository:
    return ReimbursementRepository(client)

def get_audit_repo(client: Client = Depends(get_db_client)) -> AuditLogRepository:
    return AuditLogRepository(client)

def get_auth_service(repo: ProfileRepository = Depends(get_profile_repo)) -> AuthService:
    return AuthService(repo)

def get_audit_service(repo: AuditLogRepository = Depends(get_audit_repo)) -> AuditService:
    return AuditService(repo)

def get_storage_service(client: Client = Depends(get_db_client)) -> StorageService:
    return StorageService(client)

def get_reimbursement_service(repo: ReimbursementRepository = Depends(get_reimbursement_repo), 
                              audit_service: AuditService = Depends(get_audit_service)) -> ReimbursementService:
    return ReimbursementService(repo, audit_service)

def get_zoho_service() -> ZohoExpenseService:
    return ZohoExpenseService()
