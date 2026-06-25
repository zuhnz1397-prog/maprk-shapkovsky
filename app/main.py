@app.get("/api/debug")
def debug_db():
    try:
        from app.database import SessionLocal
        from app.models.rk import RK
        db = SessionLocal()
        count = db.query(RK).count()
        db.close()
        return {"status": "ok", "rk_count": count}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}