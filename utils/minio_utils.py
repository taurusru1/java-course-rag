"""MinIO 客户端懒加载，避免服务未启动时阻塞 FastAPI 模块导入。"""

import json

from minio import Minio

from config.minio_config import minio_config

_minio_client: Minio | None = None


def get_minio_client() -> Minio:
    global _minio_client
    if _minio_client is not None:
        return _minio_client
    if not all((minio_config.endpoint, minio_config.access_key, minio_config.secret_key, minio_config.bucket_name)):
        raise RuntimeError("MinIO 配置不完整")
    client = Minio(
        endpoint=minio_config.endpoint,
        access_key=minio_config.access_key,
        secret_key=minio_config.secret_key,
        secure=False,
    )
    if not client.bucket_exists(minio_config.bucket_name):
        client.make_bucket(minio_config.bucket_name)
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow", "Principal": {"AWS": "*"}, "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{minio_config.bucket_name}/*",
        }],
    }
    client.set_bucket_policy(minio_config.bucket_name, json.dumps(policy))
    _minio_client = client
    return client
