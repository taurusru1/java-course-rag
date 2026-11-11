package com.javacourse.kb.repository;
import com.javacourse.kb.model.Course;
import org.springframework.data.jpa.repository.JpaRepository;
public interface CourseRepository extends JpaRepository<Course, Long> {}
