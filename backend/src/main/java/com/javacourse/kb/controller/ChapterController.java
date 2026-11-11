package com.javacourse.kb.controller;

import com.javacourse.kb.config.RoleGuard;
import com.javacourse.kb.model.Chapter;
import com.javacourse.kb.service.CourseService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

/** 章节维护：教师建章、改章、删章。 */
@RestController
@RequestMapping("/api/chapters")
public class ChapterController {
    private final CourseService service;

    public ChapterController(CourseService service) { this.service = service; }

    @PostMapping("/courses/{courseId}")
    public Map<String, Object> create(HttpServletRequest request, @PathVariable Long courseId, @RequestBody Chapter chapter) {
        RoleGuard.requireTeacher(request);
        Chapter saved = service.addChapter(courseId, chapter);
        return Map.of("code", 200, "data", Map.of("id", saved.getId(), "chapterNo", saved.getChapterNo()));
    }

    @PutMapping("/{id}")
    public Map<String, Object> update(HttpServletRequest request, @PathVariable Long id, @RequestBody Chapter chapter) {
        RoleGuard.requireTeacher(request);
        return Map.of("code", 200, "data", service.updateChapter(id, chapter));
    }

    @DeleteMapping("/{id}")
    public Map<String, Object> delete(HttpServletRequest request, @PathVariable Long id) {
        RoleGuard.requireTeacher(request);
        service.deleteChapter(id);
        return Map.of("code", 200, "message", "chapter deleted");
    }
}
