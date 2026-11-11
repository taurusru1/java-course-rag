package com.javacourse.kb.service;

import com.javacourse.kb.model.DiagnosticRecord;
import com.javacourse.kb.model.ErrorCase;
import com.javacourse.kb.repository.DiagnosticRecordRepository;
import com.javacourse.kb.repository.ErrorCaseRepository;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 编译/运行报错诊断：原始报错 -> 正则匹配案例库 -> 成因与修复建议 -> 落库用于评测。
 * 置信度低于 0.5 时返回空结果，前端可降级到 RAG 检索。
 */
@Service
public class DiagnoseService {
    private static final Logger log = LoggerFactory.getLogger(DiagnoseService.class);
    private final ErrorCaseRepository cases;
    private final DiagnosticRecordRepository records;

    public DiagnoseService(ErrorCaseRepository cases, DiagnosticRecordRepository records) {
        this.cases = cases;
        this.records = records;
    }

    public List<Map<String, Object>> listCases() {
        List<Map<String, Object>> result = new ArrayList<>();
        for (ErrorCase c : cases.findAll()) result.add(view(c));
        return result;
    }

    @Transactional
    public Map<String, Object> diagnose(Long userId, String rawError) {
        if (rawError == null || rawError.isBlank()) throw new IllegalArgumentException("请粘贴编译或运行报错信息");
        Match best = match(rawError);

        DiagnosticRecord record = new DiagnosticRecord();
        record.setUserId(userId);
        record.setRawError(rawError);
        record.setConfidence(best.confidence);
        if (best.errorCase != null) {
            record.setMatchedCaseId(best.errorCase.getId());
            record.setSuggestion(best.errorCase.getSolution());
        } else {
            record.setSuggestion("未命中已知错误案例，建议使用课程问答检索相关知识点。");
        }
        records.save(record);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("recordId", record.getId());
        data.put("confidence", Math.round(best.confidence * 100) / 100.0);
        data.put("matched", best.errorCase != null);
        if (best.errorCase != null) data.put("case", view(best.errorCase));
        else data.put("suggestion", record.getSuggestion());
        return data;
    }

    private record Match(ErrorCase errorCase, double confidence) {}

    private Match match(String rawError) {
        Match best = new Match(null, 0);
        for (ErrorCase c : cases.findAll()) {
            double score = score(c, rawError);
            if (score > best.confidence) best = new Match(c, score);
        }
        return best.confidence >= 0.5 ? best : new Match(null, 0);
    }

    /** 正则命中给 0.9；报错码关键词全部出现给 0.7；两者都无则 0。 */
    double score(ErrorCase c, String rawError) {
        String pattern = c.getJavacPattern();
        if (pattern != null && !pattern.isBlank()) {
            try {
                if (Pattern.compile(pattern, Pattern.CASE_INSENSITIVE | Pattern.DOTALL).matcher(rawError).find()) return 0.9;
            } catch (PatternSyntaxException e) {
                log.warn("错误的案例正则 errorCode={}: {}", c.getErrorCode(), e.getMessage());
            }
        }
        String code = c.getErrorCode();
        if (code != null && !code.isBlank()) {
            String haystack = rawError.toLowerCase().replace(" ", "_");
            boolean all = true;
            for (String token : code.toLowerCase().split("_")) {
                if (token.length() > 2 && !haystack.contains(token)) { all = false; break; }
            }
            if (all) return 0.7;
        }
        return 0;
    }

    private Map<String, Object> view(ErrorCase c) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", c.getId());
        map.put("errorCode", c.getErrorCode());
        map.put("category", c.getCategory());
        map.put("cause", c.getCause());
        map.put("solution", c.getSolution());
        map.put("knowledgePointId", c.getKnowledgePointId());
        map.put("exampleCode", c.getExampleCode());
        return map;
    }

    @Transactional
    public Map<String, Object> create(ErrorCase input) {
        if (input.getErrorCode() == null || input.getErrorCode().isBlank()) throw new IllegalArgumentException("errorCode 不能为空");
        cases.findByErrorCode(input.getErrorCode()).ifPresent(existing -> {
            throw new IllegalArgumentException("错误码已存在：" + existing.getErrorCode());
        });
        return view(cases.save(input));
    }

    /** 案例按类别聚合，方便前端做"报错知识树"。 */
    public List<Map<String, Object>> groupedCases() {
        List<ErrorCase> all = new ArrayList<>(cases.findAll());
        all.sort(Comparator.comparing(ErrorCase::getCategory, Comparator.nullsLast(String::compareTo)));
        List<Map<String, Object>> groups = new ArrayList<>();
        String current = null;
        List<Map<String, Object>> bucket = null;
        for (ErrorCase c : all) {
            if (current == null || !current.equals(c.getCategory())) {
                current = c.getCategory();
                bucket = new ArrayList<>();
                groups.add(Map.of("category", current == null ? "未分类" : current, "cases", bucket));
            }
            bucket.add(view(c));
        }
        return groups;
    }
}
