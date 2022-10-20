from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse
from requests import Response
import uvicorn


from starlette.requests import Request
from starlette.templating import Jinja2Templates
 
 
from . import db
# import db


# Models
from .models import Task
# from models import Task

from .bovespa.b3 import codigos
# from bovespa.b3 import codigos

 
app = FastAPI(
  title='Aplicação ToDo-B3 feita com FastAPI',
  description='Trabalho de Métodos á geis IFPI.',
  version='0.9 beta'
)


# configurações relacionadas ao modelo (jinja2)
templates = Jinja2Templates(directory="templates")
jinja_env = templates.env  # Jinja2.Environment : para filtro e configurações globais


def index(request: Request):
  task = db.session.query(Task).filter().all()
  task = [t for t in task]
  
  
  return templates.TemplateResponse('index.html',
                                    {'request': request,
                                     'task': task,
                                     'codigos': codigos}) 


async def get():
  """Exibição"""
  # Obter registros do usuário
  task = db.session.query(Task).filter().all()
  # db.session.commit()
  
  # lista de dados
  task = [t for t in task]
  
  return task
  

async def add(request: Request):
  
  # Obter dados do formulário HTML
  data = await request.form()
  cr_data = str(data['cr_data'])
  codigo = str(data['codigo'])
  quantidade = int(data['quantidade'])
  valor_unitario = float(data['valor_unitario'])
  tipo_op = str(data['tipo_op'])
  tx_corretagem = float(data['tx_corretagem'])
  tx_b3 = float(data['tx_b3'])
  
  # Crie uma nova tarefa e confirme
  task = Task(created_date=cr_data,codigo=codigo, quantidade=quantidade, valor_unitario=valor_unitario, 
              tipo_op=tipo_op, tx_corretagem=tx_corretagem, taxa_b3=tx_b3)
  
  db.session.add(task)
  db.session.commit()
  db.session.close()
  
  task = await get()
  
  return templates.TemplateResponse("index.html", 
                                    {"request": request,
                                     'codigos': codigos,
                                     'task': task})

  


async def update(request: Request, t_id):
  
  # Obter dados do formulário HTML
  data = await request.form()
  cr_data = str(data['cr_data'])
  codigo = str(data['codigo'])
  quantidade = int(data['quantidade'])
  valor_unitario = float(data['valor_unitario'])
  tipo_op = str(data['tipo_op'])
  valor_total = valor_unitario * quantidade # Calcula o total
  tx_corretagem = float(data['tx_corretagem'])
  tx_b3 = float(data['tx_b3'])
  
  custo_b3 = (valor_total * tx_b3) / 100
  
  if tipo_op == 'compra':
    valor_operacao = valor_total + tx_corretagem + custo_b3
  else:
    valor_operacao = valor_total - tx_corretagem - custo_b3
  
  try:
    db.session.query(Task).filter(Task.id == t_id).\
      update({Task.cr_data: cr_data,
              Task.codigo: codigo,
              Task.quantidade: quantidade,
              Task.valor_unitario: valor_unitario,
              Task.tipo_op: tipo_op,
              Task.valor_total: valor_total,
              Task.valor_operacao: valor_operacao,
              Task.tx_corretagem: tx_corretagem,
              Task.tx_b3: custo_b3}, synchronize_session='evaluate')
      
  except:
    """Problema resolvido: rollback não é executado até que chamemos rollback 
    explicitamente a 'session.query' """
    db.session.rollback()
    
  
  db.session.commit()
  db.session.close()
  
  return RedirectResponse("/")



async def delete(request: Request, t_id):
  
  # Obter tarefa correspondente e excluir
  try:
    db.session.query(Task).filter(Task.id == t_id).delete()
  except:
    """Problema resolvido: rollback não é executado até que chamemos rollback 
    explicitamente a 'session.query' """
    db.session.rollback()

  db.session.commit()
  db.session.close()
  
  # Atualisa lista
  task = await get()

  return templates.TemplateResponse("index.html", 
                                    {"request": request,
                                     "task": task,
                                     "codigos": codigos})


async def filtrar(request: Request):
  """Exibir apenas as ações expecíficas"""
  
  # Obter dados do formulário HTML
  data = await request.form()
  try:
    if data['codigo'] == "todos": 
      return RedirectResponse("/")
    else:
      task = db.session.query(Task).filter(Task.codigo == data['codigo'])
  except:
    db.session.rollback()
    
  db.session.commit()
  db.session.close()
  # lista de dados
  task = [t for t in task]
  
  return templates.TemplateResponse("index.html", 
                                    {"request": request,
                                     "task": task,
                                     "codigos": codigos})


async def analise(request: Request):
  task = db.session.query(Task).filter().all()
  ativos_comprados = db.session.query(Task).filter(Task.tipo_op == "compra")
  codigos = [v.codigo for v in ativos_comprados]
  
  return templates.TemplateResponse("analise.html",
                                    {"request": request,
                                     "task": task,
                                     "status": True,
                                     "codigos": codigos})


async def preco_medio(request: Request):
  """Calcular preco medio do ativo adiquirido"""
  
  # Obter dados do formulário HTML
  data = await request.form()
  ativo = data['codigo']
  custos = 0
  qtd = 0
  status = False
  try:
    ativos_comprados = db.session.query(Task).filter(Task.tipo_op == "compra")
    codigos = [v.codigo for v in ativos_comprados]
    # Calcular preco médio do ativo 
    valores_ativo = db.session.query(Task).filter(Task.codigo == ativo)
    try:
      for t in valores_ativo:
        if t.tipo_op == "compra":
          custos += t.valor_operacao
          qtd += t.quantidade
          status = True
      if custos and qtd != 0:
        pmedio = custos / qtd
      else:
        pmedio = "Não teve compra"
    except:
      pmedio = "Não teve compra"
  except:
    db.session.rollback()
    
  db.session.commit()
  db.session.close()
  # lista de dados
  # ativo = [t for t in ativo]
  
  
  
  
  
  return templates.TemplateResponse("analise.html", 
                                    {"request": request,
                                     "ativo": ativo,
                                     "status": status,
                                     "preco_medio": pmedio,
                                     "codigos": codigos})
  