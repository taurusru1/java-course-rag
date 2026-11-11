package com.javacourse.kb.service;

import io.minio.*;
import java.io.InputStream;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class StorageService {
    private final MinioClient client; private final String bucket; private final String endpoint;
    public StorageService(@Value("${minio.endpoint}") String endpoint,@Value("${minio.access-key}") String access,@Value("${minio.secret-key}") String secret,@Value("${minio.bucket}") String bucket){
        this.endpoint=endpoint;this.bucket=bucket;this.client=MinioClient.builder().endpoint(endpoint).credentials(access,secret).build();
    }
    public String upload(String objectName, InputStream stream, long size, String contentType) throws Exception {
        if(!client.bucketExists(BucketExistsArgs.builder().bucket(bucket).build())) client.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
        client.putObject(PutObjectArgs.builder().bucket(bucket).object(objectName).stream(stream,size,-1).contentType(contentType).build());
        return endpoint+"/"+bucket+"/"+objectName;
    }
}
