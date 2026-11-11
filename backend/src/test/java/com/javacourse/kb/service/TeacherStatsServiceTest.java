package com.javacourse.kb.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

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
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class TeacherStatsServiceTest {
    @Mock CourseRepository courses;
    @Mock QuestionRepository questions;
    @Mock KnowledgePointRepository points;
    @Mock AnswerRecordRepository answers;
    @Mock UserAccountRepository accounts;

    TeacherStatsService service;

    @BeforeEach
    void setUp() {
        service = new TeacherStatsService(courses, questions, points, answers, accounts);
    }

    private static Question question(long id, Long pointId, String stem) {
        Question q = mock(Question.class);
        when(q.getId()).thenReturn(id);
        when(q.getKnowledgePointId()).thenReturn(pointId);
        when(q.getStem()).thenReturn(stem);
        when(q.getType()).thenReturn("CHOICE");
        return q;
    }

    private static AnswerRecord record(long questionId, long userId, boolean correct) {
        AnswerRecord r = mock(AnswerRecord.class);
        when(r.getQuestionId()).thenReturn(questionId);
        when(r.getUserId()).thenReturn(userId);
        when(r.getCorrect()).thenReturn(correct);
        return r;
    }

    @Test
    @SuppressWarnings("unchecked")
    void aggregatesByKnowledgePointQuestionAndStudent() {
        Course course = mock(Course.class);
        when(course.getName()).thenReturn("Java 程序设计");
        when(courses.findById(1L)).thenReturn(Optional.of(course));

        Question q1 = question(11L, 7L, "下列哪个是合法标识符？");
        Question q2 = question(12L, null, "BufferedReader 的作用？");
        when(questions.findByCourseIdOrderByIdAsc(1L)).thenReturn(List.of(q1, q2));

        KnowledgePoint point = mock(KnowledgePoint.class);
        when(point.getId()).thenReturn(7L);
        when(point.getName()).thenReturn("变量与数据类型");
        when(points.findByCourseIdOrderByIdAsc(1L)).thenReturn(List.of(point));

        AnswerRecord r1 = record(11L, 100L, true);
        AnswerRecord r2 = record(11L, 100L, false);
        AnswerRecord r3 = record(12L, 100L, true);
        AnswerRecord other = record(99L, 100L, false);   // 其他课程的记录应被忽略
        when(answers.findAll()).thenReturn(List.of(r1, r2, r3, other));

        UserAccount student = mock(UserAccount.class);
        when(student.getId()).thenReturn(100L);
        when(student.getDisplayName()).thenReturn("李同学");
        when(accounts.findAllById(any())).thenReturn(List.of(student));

        Map<String, Object> result = service.overview(1L);
        Map<String, Object> summary = (Map<String, Object>) result.get("summary");

        assertThat(summary.get("answered")).isEqualTo(3L);
        assertThat(summary.get("wrong")).isEqualTo(1L);
        assertThat(summary.get("accuracy")).isEqualTo(0.667);
        assertThat(summary.get("students")).isEqualTo(1);
        assertThat(summary.get("questions")).isEqualTo(2);
        assertThat(summary.get("coveredQuestions")).isEqualTo(2);

        List<Map<String, Object>> byPoint = (List<Map<String, Object>>) result.get("byKnowledgePoint");
        assertThat(byPoint).hasSize(2);
        Map<String, Object> named = byPoint.stream()
            .filter(row -> "变量与数据类型".equals(row.get("label"))).findFirst().orElseThrow();
        assertThat(named.get("answered")).isEqualTo(2L);
        assertThat(named.get("wrong")).isEqualTo(1L);
        assertThat(named.get("accuracy")).isEqualTo(0.5);
        assertThat(byPoint).anyMatch(row -> "未归类".equals(row.get("label")));

        List<Map<String, Object>> hardest = (List<Map<String, Object>>) result.get("hardestQuestions");
        assertThat(hardest).hasSize(2);
        assertThat(hardest.get(0).get("accuracy")).isEqualTo(0.5);
        assertThat(hardest.get(1).get("accuracy")).isEqualTo(1.0);

        List<Map<String, Object>> students = (List<Map<String, Object>>) result.get("byStudent");
        assertThat(students).hasSize(1);
        assertThat(students.get(0).get("name")).isEqualTo("李同学");
        assertThat(students.get(0).get("answered")).isEqualTo(3L);
        assertThat(students.get(0).get("wrong")).isEqualTo(1L);
        assertThat(students.get(0).get("accuracy")).isEqualTo(0.667);
    }

    @Test
    void rejectsUnknownCourse() {
        when(courses.findById(404L)).thenReturn(Optional.empty());
        org.assertj.core.api.Assertions.assertThatThrownBy(() -> service.overview(404L))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("course not found");
    }
}
