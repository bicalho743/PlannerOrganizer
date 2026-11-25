# API local para gravar as telas reais do app: qualquer token vira a conta demo_landing (banco de TESTE)
import os, sys
sys.path.insert(0, "/home/user/PlannerOrganizer")
import api.router as router
from fastapi.middleware.cors import CORSMiddleware
router.api.dependency_overrides[router.verify_firebase_token] = lambda: "demo_landing"
router._em_modo_consulta = lambda uid: False
router.api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
api = router.api
