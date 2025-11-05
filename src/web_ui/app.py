from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from typing import Dict

security = HTTPBasic()

def create_web_app(trading_app):
    app = FastAPI(title="Binance Quant Trading", version="2.0.0")
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 认证依赖
    def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
        correct_username = secrets.compare_digest(
            credentials.username, 
            trading_app.config['web_ui']['username']
        )
        correct_password = secrets.compare_digest(
            credentials.password,
            trading_app.config['web_ui']['password']
        )
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=401,
                detail="认证失败",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username
    
    @app.get("/")
    async def root():
        return {"message": "Binance Quant Trading API", "version": "2.0.0"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "running": trading_app.running}
    
    @app.get("/status")
    async def get_status(_: str = Depends(authenticate)):
        return trading_app.get_status()
    
    @app.get("/strategies")
    async def get_strategies(_: str = Depends(authenticate)):
        return {
            "enabled": list(trading_app.components['strategy_manager'].strategies.keys()),
            "symbols": trading_app.config['trading']['symbols']
        }
    
    @app.post("/strategies/{strategy_name}/toggle")
    async def toggle_strategy(strategy_name: str, _: str = Depends(authenticate)):
        # 实现策略启停控制
        return {"message": f"Strategy {strategy_name} toggled"}
    
    @app.get("/performance")
    async def get_performance(_: str = Depends(authenticate)):
        stats = await trading_app.components['strategy_manager'].get_performance_stats()
        return stats
    
    @app.get("/positions")
    async def get_positions(_: str = Depends(authenticate)):
        positions = await trading_app.components['position_manager'].get_active_positions()
        return positions
    
    return app
