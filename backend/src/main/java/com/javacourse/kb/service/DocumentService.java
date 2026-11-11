package com.javacourse.kb.service;

import com.javacourse.kb.client.AiModuleClient;
import com.javacourse.kb.model.*;
import com.javacourse.kb.repository.DocumentRepository;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

/**
 * 讲义资料管理。
 *
 * <p>不依赖 MinIO / Milvus：上传的文件直接落到共享目录（见 app.upload-dir），
 * 再交给 Python 离线服务做「解析 → 切分 → 向量化 → 入本地索引」。
 * 这样在纯本机环境下也能演示「老师加一份讲义，学生马上能问到」。</p>
 */
@Service
public class DocumentService {
    private final DocumentRepository repository;
    private final CourseService courses;
    private final AiModuleClient ai;
    private final String uploadDir;

    public DocumentService(DocumentRepository r, CourseService c, AiModuleClient a,
                           @Value("${app.upload-dir}") String uploadDir) {
        this.repository = r;
        this.courses = c;
        this.ai = a;
        this.uploadDir = uploadDir;
    }

    @Transactional
    public Document upload(MultipartFile file, Long courseId, String docType) throws Exception {
        Course course = courses.get(courseId);
        String original = Optional.ofNullable(file.getOriginalFilename()).orElse("upload.md");
        String safeName = original.replaceAll("[\\\\/:*?\"<>|\\s]+", "_");
        Path dir = Paths.get(uploadDir).toAbsolutePath().normalize();
        Files.createDirectories(dir);
        Path target = dir.resolve(UUID.randomUUID().toString().substring(0, 8) + "-" + safeName);
        try (InputStream in = file.getInputStream()) {
            Files.copy(in, target, StandardCopyOption.REPLACE_EXISTING);
        }

        Document d = new Document();
        d.setCourse(course);
        d.setFileName(original);
        d.setFileSize(file.getSize());
        d.setDocType(docType);
        d.setStatus("processing");
        d = repository.save(d);

        Map response = ai.startImport(target.toString(), courseId, course.getName(), docType);
        d.setTaskId(String.valueOf(response.get("taskId")));
        d.setStatus("completed".equals(response.get("status")) ? "completed" : "failed");
        return repository.save(d);
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> list(Long courseId) {
        List<Document> documents = courseId == null
            ? repository.findAll()
            : repository.findByCourseIdOrderByCreatedAtDesc(courseId);
        List<Map<String, Object>> rows = new ArrayList<>();
        for (Document d : documents) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", d.getId());
            row.put("fileName", d.getFileName());
            row.put("fileSize", d.getFileSize());
            row.put("docType", d.getDocType());
            row.put("status", d.getStatus());
            row.put("taskId", d.getTaskId());
            row.put("courseId", d.getCourse().getId());
            row.put("courseName", d.getCourse().getName());
            row.put("createdAt", d.getCreatedAt());
            rows.add(row);
        }
        return rows;
    }

    @Transactional
    public void delete(Long id) {
        if (!repository.existsById(id)) throw new IllegalArgumentException("document not found");
        repository.deleteById(id);
    }

    @Transactional(readOnly = true)
    public Map<String, Object> get(Long id) {
        Document d = repository.findById(id).orElseThrow(() -> new IllegalArgumentException("document not found"));
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", d.getId());
        result.put("fileName", d.getFileName());
        result.put("status", d.getStatus());
        result.put("taskId", d.getTaskId());
        if (d.getTaskId() != null) {
            try {
                result.putAll(ai.importStatus(d.getTaskId()));
            } catch (RuntimeException e) {
                result.put("message", "AI 服务暂不可用");
            }
        }
        return result;
    }
}
