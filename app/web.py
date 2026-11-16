from fastapi import APIRouter,Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import ROOT,SAMPLE_DIR
from app import store
from app.modules.batches.service import execute
router=APIRouter()
templates=Jinja2Templates(directory=str(ROOT/"app/templates"))
PAGES=[("intake","台账采信"),("contract","计量契约"),("genealogy","投料谱系"),("recall","召回推演"),("quarantine","质量隔离"),("reconcile","物料对账"),("batches","批次归档")]
@router.get("/")
def home():return RedirectResponse("/intake")
def view(request,page):
    key=request.query_params.get("run")
    result=store.get(key) if key else execute((SAMPLE_DIR/"dirty.csv").read_bytes(),["R-0001"])
    return templates.TemplateResponse(request=request,name=page+".html",context={"data":result,"page":page,"pages":PAGES,"title":dict(PAGES)[page],"history":store.history()})
for path,_title in PAGES:
    def handler(request:Request,page=path):return view(request,page)
    router.add_api_route('/'+path,handler,methods=["GET"],name=path)
