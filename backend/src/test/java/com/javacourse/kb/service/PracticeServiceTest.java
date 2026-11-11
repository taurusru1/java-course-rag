package com.javacourse.kb.service;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.javacourse.kb.model.Question;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/** 判分规则单元测试：客观题类型不区分大小写/顺序/空白。 */
class PracticeServiceTest {
    private final PracticeService service = new PracticeService(null, null, null);

    private Question question(String type, String answer) {
        Question q = new Question();
        q.setType(type);
        q.setAnswer(answer);
        return q;
    }

    @Test
    @DisplayName("单选题忽略大小写")
    void choiceIgnoresCase() {
        assertTrue(service.judge(question("CHOICE", "B"), "b"));
        assertFalse(service.judge(question("CHOICE", "B"), "C"));
    }

    @Test
    @DisplayName("多选题忽略选项顺序")
    void multiIgnoresOrder() {
        assertTrue(service.judge(question("MULTI", "AC"), "C,A"));
        assertTrue(service.judge(question("MULTI", "A,C"), "ca"));
        assertFalse(service.judge(question("MULTI", "AC"), "AB"));
    }

    @Test
    @DisplayName("填空题忽略空白与大小写")
    void fillIgnoresWhitespace() {
        assertTrue(service.judge(question("FILL", "Integer.parseInt"), " integer. parseInt "));
        assertFalse(service.judge(question("FILL", "break"), "continue"));
    }

    @Test
    @DisplayName("空答案判错且不抛异常")
    void nullAnswerIsWrong() {
        assertFalse(service.judge(question("CHOICE", "A"), null));
        assertFalse(service.judge(question("CHOICE", null), "A"));
    }
}
