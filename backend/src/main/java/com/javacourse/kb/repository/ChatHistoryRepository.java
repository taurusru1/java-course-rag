package com.javacourse.kb.repository;
import com.javacourse.kb.model.ChatHistory; import java.util.List; import org.springframework.data.jpa.repository.JpaRepository;
public interface ChatHistoryRepository extends JpaRepository<ChatHistory,Long>{List<ChatHistory> findByStudentIdOrderByCreatedAtDesc(Long studentId); List<ChatHistory> findByStudentIdAndCategoryOrderByCreatedAtDesc(Long studentId,String category);}
