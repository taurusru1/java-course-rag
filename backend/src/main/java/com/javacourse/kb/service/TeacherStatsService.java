package com.javacourse.kb.service;

import com.javacourse.kb.model.AnswerRecord;
import com.javacourse.kb.model.Course;
import com.javacourse.kb.model.KnowledgePoint;
import com.javacourse.kb.model.Question;
import com.javacourse.kb.model.UserAccount;
import com.javacourse.kb.repository.AnswerRecordRepository;
import com.javacourse.kb.repository.CourseRepository;
import com.javacourse.kb.repository.KnowledgePointRepository;
import com.javacourse.kb.repository.QuestionRepository;
import com.javacourse.kb.repository.UserAccountRepository;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 教师端学情统计：把答题记录按知识点、题目、学生三个维度聚合。 */
@Service
public class TeacherStatsService {
    private final CourseRepository courses;
    private final QuestionRepository questions;
    private final KnowledgePointRepository points;
    private final AnswerRecordRepository answers;
    private final UserAccountRepository accounts;

    public TeacherStatsService(CourseRepository courses, QuestionRepository questions,
                               KnowledgePointRepository points, AnswerRecordRepository answers,
                               UserAccountRepository accounts) {
        this.courses = courses;
        this.questions = questions;
        this.points = points;
        this.answers = answers;
        this.accounts = accounts;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> overview(Long courseId) {
        Course course = courses.findById(courseId)
            .orElseThrow(() -> new IllegalArgumentException("course not found"));
        List<Question> courseQuestions = questions.findByCourseIdOrderByIdAsc(courseId);
        Map<Long, Question> byId = courseQuestions.stream()
            .collect(Collectors.toMap(Question::getId, q -> q));
        Map<String, String> pointNames = points.findByCourseIdOrderByIdAsc(courseId).stream()
            .collect(Collectors.toMap(p -> String.valueOf(p.getId()), KnowledgePoint::getName, (a, b) -> a));

        List<AnswerRecord> records = answers.findAll().stream()
            .filter(r -> byId.containsKey(r.getQuestionId()))
            .toList();

        // 知识点维度
        Map<String, int[]> pointStat = new LinkedHashMap<>();
        for (AnswerRecord r : records) {
            Question q = byId.get(r.getQuestionId());
            String key = q.getKnowledgePointId() == null ? "未归类" : pointNames.getOrDefault(String.valueOf(q.getKnowledgePointId()), "未归类");
            int[] cell = pointStat.computeIfAbsent(key, k -> new int[2]);
            cell[0]++;
            if (Boolean.FALSE.equals(r.getCorrect())) cell[1]++;
        }
        List<Map<String, Object>> byPoint = pointStat.entrySet().stream()
            .map(e -> row(e.getKey(), e.getValue()[0], e.getValue()[1]))
            .sorted((a, b) -> Long.compare(num(b.get("answered")), num(a.get("answered"))))
            .toList();

        // 题目维度：取最难的五道
        Map<Long, int[]> questionStat = new LinkedHashMap<>();
        for (AnswerRecord r : records) {
            int[] cell = questionStat.computeIfAbsent(r.getQuestionId(), k -> new int[2]);
            cell[0]++;
            if (Boolean.FALSE.equals(r.getCorrect())) cell[1]++;
        }
        List<Map<String, Object>> hardest = questionStat.entrySet().stream()
            .map(e -> {
                Question q = byId.get(e.getKey());
                Map<String, Object> row = row(q == null ? "已删除题目" : q.getStem(), e.getValue()[0], e.getValue()[1]);
                row.put("questionId", e.getKey());
                row.put("type", q == null ? "" : q.getType());
                return row;
            })
            .sorted((a, b) -> {
                int byAccuracy = Double.compare((double) a.get("accuracy"), (double) b.get("accuracy"));
                if (byAccuracy != 0) return byAccuracy;
                return Long.compare(num(b.get("answered")), num(a.get("answered")));
            })
            .limit(5)
            .toList();

        // 学生维度
        Map<Long, List<AnswerRecord>> byStudent = records.stream()
            .collect(Collectors.groupingBy(AnswerRecord::getUserId, LinkedHashMap::new, Collectors.toList()));
        Map<Long, String> names = accounts.findAllById(byStudent.keySet()).stream()
            .collect(Collectors.toMap(UserAccount::getId, UserAccount::getDisplayName));
        List<Map<String, Object>> students = byStudent.entrySet().stream()
            .map(e -> {
                long total = e.getValue().size();
                long wrong = e.getValue().stream().filter(r -> Boolean.FALSE.equals(r.getCorrect())).count();
                Map<String, Object> row = new LinkedHashMap<>();
                row.put("userId", e.getKey());
                row.put("name", names.getOrDefault(e.getKey(), "用户 " + e.getKey()));
                row.put("answered", total);
                row.put("wrong", wrong);
                row.put("accuracy", ratio(total - wrong, total));
                return row;
            })
            .sorted((a, b) -> Long.compare(num(b.get("answered")), num(a.get("answered"))))
            .toList();

        long total = records.size();
        long wrong = records.stream().filter(r -> Boolean.FALSE.equals(r.getCorrect())).count();

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("answered", total);
        summary.put("wrong", wrong);
        summary.put("accuracy", ratio(total - wrong, total));
        summary.put("students", students.size());
        summary.put("questions", courseQuestions.size());
        summary.put("coveredQuestions", questionStat.size());

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("courseId", courseId);
        result.put("courseName", course.getName());
        result.put("summary", summary);
        result.put("byKnowledgePoint", byPoint);
        result.put("hardestQuestions", hardest);
        result.put("byStudent", students);
        return result;
    }

    private static long num(Object value) {
        return value instanceof Number n ? n.longValue() : 0L;
    }
    private static Map<String, Object> row(String label, long answered, long wrong) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("label", label);
        row.put("answered", answered);
        row.put("wrong", wrong);
        row.put("accuracy", ratio(answered - wrong, answered));
        return row;
    }

    private static double ratio(long correct, long total) {
        if (total <= 0) return 0.0;
        return Math.round(correct * 1000.0 / total) / 1000.0;
    }
}
