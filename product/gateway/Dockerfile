FROM python:3.12.10-slim

WORKDIR /app
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY product/gateway/requirements.txt /tmp/mwd-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/mwd-requirements.txt \
    && groupadd --system mwd && useradd --system --gid mwd mwd \
    && install -d -o mwd -g mwd /state
COPY src/patent_to_pilot/__init__.py /app/src/patent_to_pilot/
COPY src/patent_to_pilot/budget/*.py /app/src/patent_to_pilot/budget/
COPY product/gateway/*.py /app/product/gateway/
COPY product/demo/ /app/product/demo/

USER mwd
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "product.gateway.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--no-access-log"]
