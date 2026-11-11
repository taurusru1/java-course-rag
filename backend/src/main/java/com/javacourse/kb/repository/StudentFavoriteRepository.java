package com.javacourse.kb.repository;
import com.javacourse.kb.model.StudentFavorite; import java.util.List; import org.springframework.data.jpa.repository.JpaRepository;
public interface StudentFavoriteRepository extends JpaRepository<StudentFavorite,Long>{List<StudentFavorite> findByStudentIdOrderByCreatedAtDesc(Long studentId);}
