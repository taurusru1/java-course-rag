package com.javacourse.kb.repository;

import com.javacourse.kb.model.ErrorCase;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ErrorCaseRepository extends JpaRepository<ErrorCase,Long> {
    Optional<ErrorCase> findByErrorCode(String errorCode);
    List<ErrorCase> findByCategoryOrderByIdAsc(String category);
}
