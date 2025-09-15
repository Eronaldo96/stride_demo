import os
import base64
from openai import AzureOpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse
import tempfile 
from pathlib import Path

env_path = Path(__file__).resolve(strict=True).parent / '.env'
load_dotenv(dotenv_path=env_path)

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_vERSION = os.getenv("AZURE_OPENAI_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],)

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version = AZURE_OPENAI_vERSION,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME)

def criar_prompt_modelo_ameacas(tipo_aplicacao,
                                autenticacao,
                                acesso_internet,
                                dados_sensiveis,
                                descricao_aplicacao
                            ):
    prompt = f"""
    Você é um especialista em segurança cibernética. Sua tarefa é analisar o seguinte modelo de ameaças e identificar possíveis vulnerabilidades e riscos associados a ele. Forneça uma análise detalhada e sugestões para mitigar esses riscos.

    Modelo de Ameaças:
    {modelo_ameacas}

    Análise:
    """
    return prompt


@app.post("/analisar_modelo_ameacas")
async def analisar_ameacas(
    imagem: UploadFile = File(...),
    tipo_aplicacao: str = Form(...),
    autenticacao: str = Form(...),
    acesso_internet: str = Form(...),
    dados_sensiveis: str = Form(...),
    descricao_aplicacao: str = Form(...)
):
    try:
        modelo_ameacas = {
            "tipo_aplicacao": tipo_aplicacao,
            "autenticacao": autenticacao,
            "acesso_internet": acesso_internet,
            "dados_sensiveis": dados_sensiveis,
            "descricao_aplicacao": descricao_aplicacao
        }

        prompt = criar_prompt_modelo_ameacas(
            tipo_aplicacao,
            autenticacao,
            acesso_internet,
            dados_sensiveis,
            descricao_aplicacao
        )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(imagem.filename).suffix) as temp_file:
            content = await imagem.read()
            temp_file.write(await imagem.read())
            temp_file_path = temp_file.name
            
        with open(temp_file.name, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        

        chat_prompt = [
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": {"type": "text", "text": prompt}},
                {"role": "user", "content": {"type": "image", "image": {"base64": encoded_string, "caption": "Diagrama do modelo de ameaças"}}}
                
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_prompt
            max_tokens=1500,
            temperature=0.95
        )

        analise = response.choices[0].message['content'].strip()
        
        os.remove(temp_file_path)

        return JSONResponse(content={"analise": analise})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)