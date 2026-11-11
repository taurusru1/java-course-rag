package com.javacourse.kb.service;

import io.minio.*;
import java.io.InputStream;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * MinIO 对象存储。客户端延迟创建：
 * 未配置密钥时应用仍可启动（知识库上传功能降级），避免开发环境因缺少存储而整体起不来。
 */
@Service
public class StorageService {
    private final String bucket; private final String endpoint;
    private final String access; private final String secret;
    private volatile MinioClient client;

    public StorageService(@Value("${minio.endpoint}") String endpoint,@Value("${minio.access-key}") String access,
                          @Value("${minio.secret-key}") String secret,@Value("${minio.bucket}") String bucket){
        this.endpoint=endpoint;this.bucket=bucket;this.access=access;this.secret=secret;
    }

    private MinioClient client(){
        MinioClient c=client;
        if(c!=null) return c;
        synchronized(this){
            if(client==null){
                if(access==null||access.isBlank()||secret==null||secret.isBlank())
                    throw new IllegalStateException("MinIO 未配置：请设置环境变量 MINIO_ACCESS_KEY / MINIO_SECRET_KEY");
                client=MinioClient.builder().endpoint(endpoint).credentials(access,secret).build();
            }
            return client;
        }
    }

    public String upload(String objectName, InputStream stream, long size, String contentType) throws Exception {
        MinioClient c=client();
        if(!c.bucketExists(BucketExistsArgs.builder().bucket(bucket).build())) c.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
        c.putObject(PutObjectArgs.builder().bucket(bucket).object(objectName).stream(stream,size,-1).contentType(contentType).build());
        return endpoint+"/"+bucket+"/"+objectName;
    }
}
