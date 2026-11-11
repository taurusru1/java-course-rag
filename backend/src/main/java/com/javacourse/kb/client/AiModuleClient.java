package com.javacourse.kb.client;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import java.net.URI;
import java.net.http.*;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class AiModuleClient {

    private final String baseUrl;
    private final ObjectMapper mapper = new ObjectMapper();
    private final java.net.http.HttpClient http = java.net.http.HttpClient.newBuilder()
        .version(java.net.http.HttpClient.Version.HTTP_1_1)
        .build();

    public AiModuleClient(@Value("${ai.service.base-url}") String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public Map startImport(String fileUrl, Long courseId, String courseName, String docType) {
        return post("/ai/import/start", Map.of(
            "fileUrl", fileUrl,
            "courseId", String.valueOf(courseId),
            "courseName", courseName,
            "docType", docType
        ));
    }

    public Map importStatus(String taskId) {
        return get("/ai/import/" + taskId + "/status");
    }

    public Map startQuery(String query, Long courseId, String sessionId) {
        return post("/ai/query/start", Map.of(
            "query", query,
            "courseId", courseId == null ? "" : String.valueOf(courseId),
            "sessionId", sessionId
        ));
    }

    public Map queryStatus(String taskId) {
        return get("/ai/query/" + taskId + "/status");
    }

    public Map querySessions() {
        return get("/ai/query/sessions");
    }

    public Map querySessionMessages(String sessionId) {
        return get("/ai/query/sessions/" + sessionId + "/messages");
    }

    public Map deleteQuerySession(String sessionId) {
        return delete("/ai/query/sessions/" + sessionId);
    }

    public InputStream queryStream(String taskId) {
        try {
            return HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(URI.create(baseUrl + "/ai/query/" + taskId + "/stream")).GET().build(),
                HttpResponse.BodyHandlers.ofInputStream()
            ).body();
        } catch (Exception e) {
            throw new AiUnavailableException();
        }
    }

    private Map post(String path, Object body) {
        try {
            String json = mapper.writeValueAsString(body);
            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .header("Content-Type", "application/json")
                .POST(java.net.http.HttpRequest.BodyPublishers.ofString(json))
                .build();
            java.net.http.HttpResponse<String> response = http
                .send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
            return mapper.readValue(response.body(), Map.class);
        } catch (Exception e) {
            throw new AiUnavailableException();
        }
    }

    private Map get(String path) {
        try {
            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .GET()
                .build();
            java.net.http.HttpResponse<String> response = http
                .send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
            return mapper.readValue(response.body(), Map.class);
        } catch (Exception e) {
            throw new AiUnavailableException();
        }
    }

    private Map delete(String path) {
        try {
            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + path))
                .DELETE()
                .build();
            java.net.http.HttpResponse<String> response = http
                .send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
            return mapper.readValue(response.body(), Map.class);
        } catch (Exception e) {
            throw new AiUnavailableException();
        }
    }

    public static class AiUnavailableException extends RuntimeException {
        public AiUnavailableException() {
            super("AI service unavailable");
        }
    }
}
