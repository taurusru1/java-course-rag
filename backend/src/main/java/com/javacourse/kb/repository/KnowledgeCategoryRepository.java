package com.javacourse.kb.repository;
import com.javacourse.kb.model.KnowledgeCategory; import java.util.List; import org.springframework.data.jpa.repository.JpaRepository;
public interface KnowledgeCategoryRepository extends JpaRepository<KnowledgeCategory,Long>{List<KnowledgeCategory> findByEnabledTrueOrderBySortOrderAsc();}
