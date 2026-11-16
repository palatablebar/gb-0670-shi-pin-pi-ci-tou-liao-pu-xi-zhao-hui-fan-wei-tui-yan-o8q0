from fastapi import APIRouter,Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import ROOT,SAMPLE_DIR
from app import store
from app.modules.batches.service import execute
router=APIRouter()
templates=Jinja2Templates(directory=str(ROOT/"app/templates"))
PAGES=[("intake","台账采信"),("contract","计量契约"),("genealogy","投料谱系"),("recall","召回推演"),("quarantine","质量隔离"),("reconcile","物料对账"),("batches","批次归档")]
STATE_LABEL={"keep":"保留","remove":"移除","review":"待核查"}
@router.get("/")
def home():return RedirectResponse("/intake")
def view(request,page):
    key=request.query_params.get("run")
    result=store.get(key) if key else execute((SAMPLE_DIR/"dirty.csv").read_bytes(),["R-0001"])
    return templates.TemplateResponse(request=request,name=page+".html",context={"data":result,"page":page,"pages":PAGES,"title":dict(PAGES)[page],"history":store.history()})
for path,_title in PAGES:
    def handler(request:Request,page=path):return view(request,page)
    router.add_api_route('/'+path,handler,methods=["GET"],name=path)
def _layout_view(result):
    # 共享布局按单次运行（runs）结构取值；修订记录补齐兼容视图，原始 payload 仍以 data 暴露给子模板。
    is_amendment = "amendment_id" in result["manifest"]
    if is_amendment:
        view = dict(result)
        view["manifest"] = {**result["manifest"],
                            "run_id": result["manifest"]["amendment_id"],
                            "sha256": result["manifest"]["amendment_sha256"]}
        view.setdefault("review", {"version": 1, "state": "amendment", "note": ""})
        return view
    return result
@router.get("/amendments")
def amendment_page(request:Request):
    key=request.query_params.get("amendment")
    baseline=request.query_params.get("run")
    if key:
        result=store.get_amendment(key)
    else:
        if not baseline:
            return RedirectResponse("/recall")
        result=store.get(baseline)
    return templates.TemplateResponse(
        request=request,name="amendment.html",
        context={"data":_layout_view(result),"raw":result,"page":"amendments","pages":PAGES,
                "title":"修订裁决","history":store.history(),
                "amendment_history":store.amendment_history(),
                "state_label":STATE_LABEL,"is_amendment":key is not None})

