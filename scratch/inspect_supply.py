import sys
sys.path.insert(0, 'd:/FMCG_P/AFX_FMCG_BE')
from dotenv import load_dotenv
load_dotenv('d:/FMCG_P/AFX_FMCG_BE/.env')

from app import create_app
from app.db import get_db, jload
sys.stdout.reconfigure(encoding='utf-8')


app = create_app()
with app.app_context():
    db = get_db()
with app.app_context():
    db = get_db()
    qs = db.query('SELECT * FROM chat_questions WHERE conversation_id = 6 ORDER BY seq ASC')
    print('QUESTIONS:')
    for q in qs:
        print(f"[{q['id']}] seq={q['seq']} status={q['status']} is_followup={q['is_followup']} node_key={q['node_key']} topic={q['topic']}\n  Q: {q['question_text']}\n  A: {q['answer_text']}\n  ops: {q['extracted_ops']}\n")

    msgs = db.query('SELECT * FROM conversation_messages WHERE conversation_id = 6 ORDER BY id ASC')
    print(f'MESSAGES (Total {len(msgs)}):')
    for m in msgs:
        print(f"[{m['id']}] {m['role']} ({m['kind']}): {str(m['content'])[:120]}... meta={m['meta']}")


