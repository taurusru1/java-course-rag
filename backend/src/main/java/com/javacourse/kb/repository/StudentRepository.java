package com.javacourse.kb.repository;
import com.javacourse.kb.model.Student; import org.springframework.data.jpa.repository.JpaRepository;
public interface StudentRepository extends JpaRepository<Student,Long>{}
