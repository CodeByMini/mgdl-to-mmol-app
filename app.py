from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse

from typing import List, Union
from pydantic import BaseModel
from datetime import datetime

import os
import uvicorn
from pathlib import Path
from io import StringIO

origins = ["*"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


@app.get("/", response_class=HTMLResponse)
async def Index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Diabetes 101",
        },
    )


@app.post("/files/")
async def create_files(
    title: str = Form(), timeFormat: str = Form(), file: UploadFile = File()
):
    dates = []
    values = []
    f = await file.read()
    decoded = f.decode("utf8")
    rows = decoded.split("\r\n")
    for row in rows:
        item = row.split(";")
        if len(item[0]) > 1:
            dates.append(datetime.strptime(item[0], timeFormat))
            values.append(float(item[1]) / 18)

    writer = StringIO()
    firstrow = "Glukosuppgifter,Skapat den,,Skapat av,\n"
    secondrow = "Enhet,Serienummer,Enhetens tidsstämpel,Registertyp,Historiskt glukosvärde mmol/L,Skanna glukosvärde mmol/L,Icke-numeriskt snabbverkande insulin,Snabbverkande insulin (enheter),Icke-numerisk mat,Kolhydrater (gram),Kolhydrater (portioner),Icke-numeriskt långtidsverkande insulin,Långtidsverkande insulin (enheter),Anteckningar,Glukossticka mmol/L,Keton mmol/L,Måltidsinsulin (enheter),Korrigeringsinsulin (enheter),Användarändrat insulin (enheter)\n"

    writer.writelines(firstrow)
    writer.writelines(secondrow)
    for i in range(len(dates)):
        line = (
            "Nightscout,"
            + title
            + ","
            + str(dates[i])
            + ',0,"'
            + str(values[i])
            + '",,,'
            + ",,,,,,,,,,,\n"
        )
        writer.writelines(line)

    writer.seek(0)
    export_media_type = "text/csv"
    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}.csv".format(
            file_name=title
        )
    }
    return StreamingResponse(
        writer, headers=export_headers, media_type=export_media_type
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
