package com.javacourse.kb.controller;

import com.javacourse.kb.model.Question;
import com.javacourse.kb.model.UserAccount;
import com.javacourse.kb.repository.QuestionRepository;
import com.javacourse.kb.service.PracticeService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Map;
import org.springframework.web.bind.annotation.*;

/** 练习与错题：出题、判分、错题溯源、学习统计。 */
@RestController
@RequestMapping("/api/practice")
public class PracticeController {
    private final PracticeService practice;
    private final QuestionRepository questions;

    public PracticeController(PracticeService practice, QuestionRepository questions) {
        this.practice = practice;
        this.questions = questions;
    }

    public record SubmitRequest(Long questionId, String answer) {}

    @GetMapping("/questions")
    public Map<String, Object> list(@RequestParam(required = false) Long courseId,
                                    @RequestParam(required = false) Long chapterId) {
        return Map.of("code", 200, "data", practice.listQuestions(courseId, chapterId));
    }

    @GetMapping("/questions/{id}")
    public Map<String, Object> detail(@PathVariable Long id) {
        return Map.of("code", 200, "data", practice.getQuestion(id));
    }

    @PostMapping("/questions")
    public Map<String, Object> create(@RequestBody Question question) {
        if (question.getCourseId() == null) throw new IllegalArgumentException("courseId 不能为空");
        if (question.getStem() == null || question.getStem().isBlank()) throw new IllegalArgumentException("题干不能为空");
        Question saved = questions.save(question);
        return Map.of("code", 200, "data", Map.of("id", saved.getId()));
    }

    @PostMapping("/submit")
    public Map<String, Object> submit(HttpServletRequest request, @RequestBody SubmitRequest body) {
        if (body.questionId() == null) throw new IllegalArgumentException("questionId 不能为空");
        return Map.of("code", 200, "data", practice.submit(userId(request), body.questionId(), body.answer()));
    }

    @GetMapping("/wrong")
    public Map<String, Object> wrong(HttpServletRequest request) {
        return Map.of("code", 200, "data", practice.wrongAnswers(userId(request)));
    }

    @GetMapping("/stats")
    public Map<String, Object> stats(HttpServletRequest request) {
        return Map.of("code", 200, "data", practice.stats(userId(request)));
    }

    static Long userId(HttpServletRequest request) {
        Object user = request.getAttribute("authUser");
        if (user instanceof UserAccount account) return account.getId();
        throw new SecurityException("未登录");
    }
}
