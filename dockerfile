FROM python:3.10-slim

WORKDIR /UPA

COPY UPA/ /UPA/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "dashboard_atendimentos.py"]