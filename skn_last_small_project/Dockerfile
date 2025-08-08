FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ARG OPENAI_API_KEY
ARG PINECONE_PJ_KEY

ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV PINECONE_PJ_KEY=$PINECONE_PJ_KEY
ENV DEBUG=False

CMD ["gunicorn", "skn_last_small_project.wsgi:application", "--bind", "0.0.0.0:8000"]