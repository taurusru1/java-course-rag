package com.javacourse.kb.repository;

import com.javacourse.kb.model.DiagnosticRecord;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DiagnosticRecordRepository extends JpaRepository<DiagnosticRecord,Long> {
    List<DiagnosticRecord> findByUserIdOrderByCreatedAtDesc(Long userId);
}
