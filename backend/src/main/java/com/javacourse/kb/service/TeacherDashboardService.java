package com.javacourse.kb.service;

import com.javacourse.kb.model.Document;
import com.javacourse.kb.repository.ChatHistoryRepository;
import com.javacourse.kb.repository.CourseRepository;
import com.javacourse.kb.repository.DocumentRepository;
import java.util.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TeacherDashboardService {
    private final CourseRepository courses;
    private final DocumentRepository documents;
    private final ChatHistoryRepository histories;

    public TeacherDashboardService(CourseRepository courses, DocumentRepository documents, ChatHistoryRepository histories) {
        this.courses = courses;
        this.documents = documents;
        this.histories = histories;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> summary() {
        List<Map<String, Object>> recent = documents.findTop8ByOrderByCreatedAtDesc().stream().map(this::documentView).toList();
        List<Map<String, Object>> courseUsage = courses.findAll().stream().map(course -> Map.<String, Object>of(
            "id", course.getId(),
            "name", course.getName(),
            "department", course.getDepartment() == null ? "未设置" : course.getDepartment(),
            "documentCount", documents.countByCourseId(course.getId())
        )).sorted((a, b) -> Long.compare((Long)b.get("documentCount"), (Long)a.get("documentCount"))).limit(6).toList();
        return Map.of(
            "courseCount", courses.count(),
            "documentCount", documents.count(),
            "doneCount", documents.countByStatus("done"),
            "processingCount", documents.countByStatus("processing"),
            "failedCount", documents.countByStatus("failed"),
            "questionCount", histories.count(),
            "recentDocuments", recent,
            "courseUsage", courseUsage
        );
    }

    private Map<String, Object> documentView(Document item) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", item.getId());
        result.put("fileName", item.getFileName());
        result.put("courseName", item.getCourse().getName());
        result.put("status", item.getStatus());
        result.put("createdAt", item.getCreatedAt());
        return result;
    }
}
