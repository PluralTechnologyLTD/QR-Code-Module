import uuid
import qrcode
import os
import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import get_database, insert_dummy_data

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    db = get_database()
    await insert_dummy_data(db)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("select_project.html", {"request": request})


@app.get("/form", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.get("/create_project", response_class=HTMLResponse)
async def create_project_page(request: Request):
    return templates.TemplateResponse("create_project.html", {"request": request})


@app.post("/submit_project", response_class=HTMLResponse)
async def submit_project(request: Request):
    form = await request.form()
    project_name = form.get("project_name")
    fov = int(form.get("fov"))
    models_used = form.get("models_used").split(",")
    db = get_database()
    existing = await db["projects"].find_one({"project_name": project_name, "fov": fov})
    if not existing:
        await db["projects"].insert_one(
            {
                "project_name": project_name,
                "fov": fov,
                "models_used": [m.strip() for m in models_used],
                "timestamp": None,
            }
        )
    return RedirectResponse(url="/form", status_code=302)


@app.post("/generate_qr/", response_class=HTMLResponse)
async def generate_qr(request: Request):
    form_data = await request.form()
    project_name = form_data.get("project_name")
    fov = int(form_data.get("fov"))
    db = get_database()
    project = await db["projects"].find_one({"project_name": project_name, "fov": fov})

    if project:
        qr_code_data = f"{project_name}-{fov}"
        qr = qrcode.make(f"http://127.0.0.1:8000/qr_info/{qr_code_data}")
        os.makedirs("static/qrcodes", exist_ok=True)
        file_name = f"{uuid.uuid4()}.png"
        path = f"static/qrcodes/{file_name}"
        qr.save(path)

        return templates.TemplateResponse(
            "qr_display.html",
            {
                "request": request,
                "qr_url": f"/{path}",
                "info_url": f"http://127.0.0.1:8000/qr_info/{qr_code_data}",
            },
        )
    else:
        return templates.TemplateResponse(
            "form.html", {"request": request, "error": "Project not found."}
        )


@app.get("/qr_info/{qr_code_data}", response_class=HTMLResponse)
async def qr_info(request: Request, qr_code_data: str):
    project_name, fov = qr_code_data.split("-")
    fov = int(fov)
    db = get_database()
    project = await db["projects"].find_one({"project_name": project_name, "fov": fov})
    if project:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await db["projects"].update_one(
            {"_id": project["_id"]}, {"$set": {"timestamp": timestamp}}
        )
        project["timestamp"] = timestamp
        return templates.TemplateResponse(
            "qr_info.html", {"request": request, "project": project}
        )
    return {"error": "Project not found"}
