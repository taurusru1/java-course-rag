package com.javacourse.kb.service;

import com.javacourse.kb.model.AnswerRecord;
import com.javacourse.kb.model.KnowledgePoint;
import com.javacourse.kb.model.Question;
import com.javacourse.kb.repository.AnswerRecordRepository;
import com.javacourse.kb.repository.KnowledgePointRepository;
import com.javacourse.kb.repository.QuestionRepository;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 练习判分与错题溯源。
 * 客观题按标准答案判分；CODE 题当前为文本比对，后续接入 javac/java 沙箱运行判题。
 */
@Service
public class PracticeService {
    private final QuestionRepository questions;
    private final AnswerRecordRepository answers;
    private final KnowledgePointRepository points;

    public PracticeService(QuestionRepository questions, AnswerRecordRepository answers, KnowledgePointRepository points) {
        this.questions = questions;
        this.answers = answers;
        this.points = points;
    }

    public List<Map<String, Object>> listQuestions(Long courseId, Long chapterId) {
        List<Question> list;
        if (chapterId != null) list = questions.findAll().stream().filter(q -> chapterId.equals(q.getChapterId())).toList();
        else if (courseId != null) list = questions.findByCourseIdOrderByIdAsc(courseId);
        else list = questions.findAll();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Question q : list) result.add(view(q, false));
        return result;
    }

    public Map<String, Object> getQuestion(Long id) { return view(load(id), false); }

    public Map<String, Object> view(Question q, boolean withAnswer) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", q.getId());
        map.put("courseId", q.getCourseId());
        map.put("chapterId", q.getChapterId());
        map.put("knowledgePointId", q.getKnowledgePointId());
        map.put("type", q.getType());
        map.put("stem", q.getStem());
        map.put("options", q.getOptionsJson());
        map.put("difficulty", q.getDifficulty());
        map.put("source", q.getSource());
        if (withAnswer) {
            map.put("answer", q.getAnswer());
            map.put("analysis", q.getAnalysis());
        }
        return map;
    }

    @Transactional
    public Map<String, Object> submit(Long userId, Long questionId, String userAnswer) {
        Question q = load(questionId);
        boolean correct = judge(q, userAnswer);
        AnswerRecord record = new AnswerRecord();
        record.setUserId(userId);
        record.setQuestionId(questionId);
        record.setUserAnswer(userAnswer);
        record.setCorrect(correct);
        record.setScore(correct ? 100 : 0);
        answers.save(record);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("recordId", record.getId());
        data.put("correct", correct);
        data.put("score", record.getScore());
        data.put("standardAnswer", q.getAnswer());
        data.put("analysis", q.getAnalysis());
        if (q.getKnowledgePointId() != null) {
            points.findById(q.getKnowledgePointId()).ifPresent(p -> data.put("knowledgePoint", knowledgeView(p)));
        }
        return data;
    }

    /** 错题列表：错题 -> 题目 -> 知识点，用于"错题溯源"。 */
    public List<Map<String, Object>> wrongAnswers(Long userId) {
        List<AnswerRecord> records = answers.findByUserIdAndCorrectFalseOrderByCreatedAtDesc(userId);
        List<Map<String, Object>> result = new ArrayList<>();
        for (AnswerRecord r : records) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("recordId", r.getId());
            item.put("userAnswer", r.getUserAnswer());
            item.put("createdAt", r.getCreatedAt());
            questions.findById(r.getQuestionId()).ifPresent(q -> {
                item.put("question", view(q, true));
                item.put("chapterId", q.getChapterId());
                if (q.getKnowledgePointId() != null) {
                    points.findById(q.getKnowledgePointId()).ifPresent(p -> item.put("knowledgePoint", knowledgeView(p)));
                }
            });
            result.add(item);
        }
        return result;
    }

    public Map<String, Object> stats(Long userId) {
        long total = answers.countByUserId(userId);
        long wrong = answers.countByUserIdAndCorrectFalse(userId);
        double accuracy = total == 0 ? 0 : (double) (total - wrong) / total;
        return Map.of("total", total, "wrong", wrong, "accuracy", Math.round(accuracy * 1000) / 1000.0);
    }

    private Map<String, Object> knowledgeView(KnowledgePoint p) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", p.getId());
        map.put("code", p.getCode());
        map.put("name", p.getName());
        map.put("chapterId", p.getChapterId());
        return map;
    }

    private Question load(Long id) {
        return questions.findById(id).orElseThrow(() -> new IllegalArgumentException("题目不存在：" + id));
    }

    boolean judge(Question q, String userAnswer) {
        String expected = q.getAnswer() == null ? "" : q.getAnswer().trim();
        String actual = userAnswer == null ? "" : userAnswer.trim();
        String type = q.getType() == null ? "" : q.getType().toUpperCase();
        return switch (type) {
            case "CHOICE", "JUDGE" -> expected.equalsIgnoreCase(actual);
            case "MULTI" -> sortedLetters(expected).equals(sortedLetters(actual));
            default -> normalize(expected).equals(normalize(actual));
        };
    }

    private String sortedLetters(String value) {
        return value == null ? "" : value.replaceAll("[^A-Za-z]", "").toUpperCase().chars()
            .sorted().collect(StringBuilder::new, StringBuilder::appendCodePoint, StringBuilder::append).toString();
    }

    private String normalize(String value) {
        return value == null ? "" : value.replaceAll("\\s+", "").toLowerCase();
    }
}
