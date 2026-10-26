import sys, time
sys.path.insert(0, 'd:/FMCG_P/AFX_FMCG_BE')
from dotenv import load_dotenv
load_dotenv('d:/FMCG_P/AFX_FMCG_BE/.env')

from app import create_app
from app.db import get_db
from app.services.chat_service import ChatService
from app.services.reference_service import ReferenceService
from app.blueprints._helpers import llm
sys.stdout.reconfigure(encoding='utf-8')

app = create_app()
with app.app_context():
    db = get_db()
    refs = ReferenceService(db)
    domain = refs.domain('supply-chain-procurement')
    svc = ChatService(db, llm())
    
    print("Testing ChatService.answer on supply-chain-procurement...")
    t0 = time.time()
    try:
        # Let's test with a simulated answer
        res = svc.answer(3, domain, "We use Multi-Echelon Safety Stock Optimization (MESSO) linking Central Warehouse to Regional Depots with min-max reorder policies.")
        print(f"SUCCESS in {time.time() - t0:.2f}s!")
        print("Progress:", res.get("progress"))
        print("Graph updated:", res.get("graph_updated"))
        if res.get("graph"):
            print(f"Nodes: {len(res['graph'].get('nodes', []))}, Edges: {len(res['graph'].get('edges', []))}")
        print("Latest message:", res.get("messages", [])[-1] if res.get("messages") else "None")
    except Exception as e:
        import traceback
        print(f"FAILED in {time.time() - t0:.2f}s with error: {e}")
        traceback.print_exc()
