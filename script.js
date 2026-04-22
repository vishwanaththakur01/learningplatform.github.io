/**
 * AI-Powered Learning Platform - Main JavaScript
 * Handles all frontend interactions, animations, and API calls
 */

// ============================================
// DOM Content Loaded
// ============================================
document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
});

function initializeApp() {
  initMobileMenu();
  initSmoothScroll();
  initAnimations();
  initFormValidations();
  initProgressTracking();
  initLearningPathway();
  initAssessment();
  initCharts();
}

/**
 * Mobile Menu Toggle
 */
function initMobileMenu() {
  const mobileMenuBtn = document.querySelector(".mobile-menu-btn");
  const navLinks = document.querySelector(".nav-links");

  if (mobileMenuBtn && navLinks) {
    mobileMenuBtn.addEventListener("click", function () {
      navLinks.classList.toggle("active");
      this.classList.toggle("active");
    });
  }
}

/**
 * Smooth Scroll for Anchor Links
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    });
  });
}

/**
 * Scroll Animations using Intersection Observer
 */
function initAnimations() {
  const animatedElements = document.querySelectorAll(
    ".feature-card, .style-card, .testimonial-card, .stat-card, .course-card",
  );

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate-in");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px",
      },
    );

    animatedElements.forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(30px)";
      observer.observe(el);
    });
  }
}

/**
 * Form Validations
 */
function initFormValidations() {
  // Login Form Validation
  const loginForm = document.querySelector(".auth-form");
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      if (!validateLoginForm(this)) {
        e.preventDefault();
      }
    });
  }

  // Register Form Validation
  const registerForm = document.querySelector(".register-card .auth-form");
  if (registerForm) {
    registerForm.addEventListener("submit", function (e) {
      if (!validateRegisterForm(this)) {
        e.preventDefault();
      }
    });
  }

  // Real-time validation for inputs
  document.querySelectorAll("input, select, textarea").forEach((input) => {
    input.addEventListener("blur", function () {
      validateField(this);
    });

    input.addEventListener("input", function () {
      if (this.classList.contains("error")) {
        validateField(this);
      }
    });
  });
}

/**
 * Validate Login Form
 */
function validateLoginForm(form) {
  let isValid = true;
  const email = form.querySelector("#email");
  const password = form.querySelector("#password");

  if (!validateEmail(email.value)) {
    showFieldError(email, "Please enter a valid email address");
    isValid = false;
  }

  if (password.value.length < 6) {
    showFieldError(password, "Password must be at least 6 characters");
    isValid = false;
  }

  return isValid;
}

/**
 * Validate Register Form
 */
function validateRegisterForm(form) {
  let isValid = true;
  const firstName = form.querySelector("#first_name");
  const lastName = form.querySelector("#last_name");
  const email = form.querySelector("#email");
  const password = form.querySelector("#password");
  const confirmPassword = form.querySelector("#confirm_password");
  const interest = form.querySelector("#interest");
  const experience = form.querySelector("#experience");
  const terms = form.querySelector('input[name="terms"]');

  if (firstName.value.trim().length < 2) {
    showFieldError(firstName, "First name must be at least 2 characters");
    isValid = false;
  }

  if (lastName.value.trim().length < 2) {
    showFieldError(lastName, "Last name must be at least 2 characters");
    isValid = false;
  }

  if (!validateEmail(email.value)) {
    showFieldError(email, "Please enter a valid email address");
    isValid = false;
  }

  if (password.value.length < 8) {
    showFieldError(password, "Password must be at least 8 characters");
    isValid = false;
  }

  if (password.value !== confirmPassword.value) {
    showFieldError(confirmPassword, "Passwords do not match");
    isValid = false;
  }

  if (!interest.value) {
    showFieldError(interest, "Please select your learning interest");
    isValid = false;
  }

  if (!experience.value) {
    showFieldError(experience, "Please select your experience level");
    isValid = false;
  }

  if (!terms.checked) {
    showFieldError(terms, "You must agree to the terms");
    isValid = false;
  }

  return isValid;
}

/**
 * Validate Individual Field
 */
function validateField(field) {
  const value = field.value.trim();
  let isValid = true;
  let errorMessage = "";

  if (field.required && !value) {
    isValid = false;
    errorMessage = "This field is required";
  } else if (field.type === "email" && !validateEmail(value)) {
    isValid = false;
    errorMessage = "Please enter a valid email address";
  } else if (field.type === "password" && value.length < 8) {
    isValid = false;
    errorMessage = "Password must be at least 8 characters";
  } else if (field.id === "first_name" || field.id === "last_name") {
    if (value.length < 2) {
      isValid = false;
      errorMessage = "Must be at least 2 characters";
    }
  }

  if (isValid) {
    clearFieldError(field);
  } else {
    showFieldError(field, errorMessage);
  }

  return isValid;
}

/**
 * Email Validation Helper
 */
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Show Field Error
 */
function showFieldError(field, message) {
  field.classList.add("error");
  field.classList.remove("valid");

  let errorEl = field.parentElement.querySelector(".field-error");
  if (!errorEl) {
    errorEl = document.createElement("div");
    errorEl.className = "field-error";
    field.parentElement.appendChild(errorEl);
  }

  errorEl.textContent = message;
  errorEl.style.display = "block";
}

/**
 * Clear Field Error
 */
function clearFieldError(field) {
  field.classList.remove("error");
  field.classList.add("valid");

  const errorEl = field.parentElement.querySelector(".field-error");
  if (errorEl) {
    errorEl.style.display = "none";
  }
}

/**
 * Password Toggle Visibility
 */
function togglePasswordVisibility(inputId, toggleId) {
  const input = document.getElementById(inputId);
  const toggle = document.getElementById(toggleId);

  if (input && toggle) {
    toggle.addEventListener("click", function () {
      const type =
        input.getAttribute("type") === "password" ? "text" : "password";
      input.setAttribute("type", type);
      this.classList.toggle("fa-eye-slash");
      this.classList.toggle("fa-eye");
    });
  }
}

// ============================================
// Progress Tracking
// ============================================
function initProgressTracking() {
  // Initialize progress bars with animation
  const progressBars = document.querySelectorAll(".progress-fill");
  progressBars.forEach((bar) => {
    const width = bar.style.width;
    bar.style.width = "0%";
    setTimeout(() => {
      bar.style.width = width;
    }, 500);
  });

  // Initialize circular progress
  const circularProgress = document.querySelectorAll(".circular-progress");
  circularProgress.forEach((progress) => {
    const value = progress.getAttribute("data-value");
    animateCircularProgress(progress, value);
  });
}

/**
 * Animate Circular Progress
 */
function animateCircularProgress(progress, value) {
  const circle = progress.querySelector(".progress-circle");
  const percentage = progress.querySelector(".progress-percentage");
  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;

  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  circle.style.strokeDashoffset = circumference;

  const offset = circumference - (value / 100) * circumference;
  circle.style.strokeDashoffset = offset;

  // Animate percentage
  let current = 0;
  const duration = 1500;
  const step = (value / duration) * 16;

  function animate() {
    current += step;
    if (current < value) {
      percentage.textContent = Math.round(current) + "%";
      requestAnimationFrame(animate);
    } else {
      percentage.textContent = value + "%";
    }
  }

  animate();
}

/**
 * Update User Progress
 */
async function updateProgress(courseId, progressData) {
  try {
    const response = await fetch("/api/progress/update", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        course_id: courseId,
        ...progressData,
      }),
    });

    const data = await response.json();

    if (data.success) {
      showNotification("Progress saved successfully!", "success");
      updateProgressUI(data.progress);
    } else {
      showNotification("Failed to save progress", "error");
    }
  } catch (error) {
    console.error("Error updating progress:", error);
    showNotification("An error occurred", "error");
  }
}

/**
 * Update Progress UI
 */
function updateProgressUI(progress) {
  // Update progress bars
  const progressBars = document.querySelectorAll(".progress-fill");
  progressBars.forEach((bar) => {
    const topic = bar
      .closest(".path-topic")
      ?.querySelector("h3")
      ?.textContent?.toLowerCase();
    if (topic && progress[topic]) {
      bar.style.width = progress[topic] + "%";
    }
  });

  // Update stats
  const statValues = document.querySelectorAll(".stat-value");
  statValues.forEach((stat) => {
    if (stat.textContent.includes("Courses")) {
      stat.textContent = progress.completed_courses;
    } else if (stat.textContent.includes("Hours")) {
      stat.textContent = progress.total_hours + "h";
    } else if (stat.textContent.includes("Streak")) {
      stat.textContent = progress.current_streak;
    } else if (stat.textContent.includes("Score")) {
      stat.textContent = progress.avg_score + "%";
    }
  });
}

// ============================================
// Learning Pathway
// ============================================
function initLearningPathway() {
  const pathwayContainer = document.getElementById("learning-pathway");
  if (!pathwayContainer) return;

  loadLearningPathway();
}

/**
 * Load Learning Pathway from API
 */
async function loadLearningPathway() {
  try {
    const response = await fetch("/api/learning-path");
    const data = await response.json();

    if (data.success) {
      renderLearningPathway(data.pathway);
    }
  } catch (error) {
    console.error("Error loading learning pathway:", error);
  }
}

/**
 * Render Learning Pathway
 */
function renderLearningPathway(pathway) {
  const container = document.getElementById("learning-pathway");
  if (!container) return;

  container.innerHTML = pathway
    .map(
      (item, index) => `
        <div class="pathway-item ${item.completed ? "completed" : ""} ${item.current ? "current" : ""}" 
             data-index="${index}">
            <div class="pathway-marker">
                ${
                  item.completed
                    ? '<i class="fas fa-check"></i>'
                    : `<span>${index + 1}</span>`
                }
            </div>
            <div class="pathway-content">
                <h4>${item.title}</h4>
                <p>${item.description}</p>
                <div class="pathway-meta">
                    <span class="duration"><i class="fas fa-clock"></i> ${item.duration} min</span>
                    <span class="type type-${item.type}">${item.type}</span>
                </div>
                <div class="pathway-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${item.progress}%"></div>
                    </div>
                    <span>${item.progress}%</span>
                </div>
            </div>
            <div class="pathway-actions">
                <button class="btn btn-primary btn-small" onclick="startCourse('${item.id}')">
                    ${item.completed ? "Review" : item.current ? "Continue" : "Start"}
                </button>
            </div>
        </div>
    `,
    )
    .join("");

  // Add animation delay
  const items = container.querySelectorAll(".pathway-item");
  items.forEach((item, index) => {
    item.style.animationDelay = `${index * 0.1}s`;
  });
}

/**
 * Start Course
 */
function startCourse(courseId) {
  window.location.href = `/course/${courseId}`;
}

/**
 * Complete Course Step
 */
async function completeCourseStep(courseId, stepId) {
  try {
    const response = await fetch("/api/course/complete-step", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        course_id: courseId,
        step_id: stepId,
      }),
    });

    const data = await response.json();

    if (data.success) {
      showNotification("Step completed! Great job!", "success");
      loadLearningPathway();

      if (data.achievement) {
        showAchievementNotification(data.achievement);
      }
    }
  } catch (error) {
    console.error("Error completing step:", error);
  }
}

// ============================================
// Assessment Functions
// ============================================
function initAssessment() {
  const assessmentForm = document.getElementById("assessment-form");
  if (!assessmentForm) return;

  assessmentForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    await submitAssessment();
  });

  // Initialize question navigation
  initQuestionNavigation();
}

/**
 * Submit Assessment
 */
async function submitAssessment() {
  const form = document.getElementById("assessment-form");
  const formData = new FormData(form);
  const responses = {};

  for (let [key, value] of formData.entries()) {
    responses[key] = value;
  }

  // Show loading state
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.innerHTML;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
  submitBtn.disabled = true;

  try {
    const response = await fetch("/api/assessment/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(responses),
    });

    const data = await response.json();

    if (data.success) {
      showAssessmentResults(data);
    } else {
      showNotification("Assessment submission failed", "error");
    }
  } catch (error) {
    console.error("Error submitting assessment:", error);
    showNotification("An error occurred", "error");
  } finally {
    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
  }
}

/**
 * Show Assessment Results
 */
function showAssessmentResults(data) {
  const resultsContainer = document.getElementById("assessment-results");
  if (!resultsContainer) return;

  resultsContainer.style.display = "block";
  resultsContainer.scrollIntoView({ behavior: "smooth" });

  // Animate results
  const learningStyle = data.learning_style;
  const confidence = data.confidence;
  const scores = data.scores;

  // Update learning style display
  const styleElement = document.getElementById("result-learning-style");
  if (styleElement) {
    styleElement.innerHTML = `
            <i class="fas fa-brain"></i>
            <span>${learningStyle.replace("_", " ").toUpperCase()}</span>
        `;
  }

  // Update confidence meter
  const confidenceElement = document.getElementById("result-confidence");
  if (confidenceElement) {
    confidenceElement.textContent = Math.round(confidence * 100) + "%";
  }

  // Update score bars
  Object.entries(scores).forEach(([style, score]) => {
    const bar = document.getElementById(`score-${style}`);
    if (bar) {
      bar.style.width = `${(score / 9) * 100}%`;
    }
  });

  // Show personalized recommendations
  const recommendationsContainer = document.getElementById(
    "personalized-recommendations",
  );
  if (recommendationsContainer && data.recommendations) {
    recommendationsContainer.innerHTML = data.recommendations
      .map(
        (rec) => `
            <div class="recommendation-card">
                <div class="rec-icon">
                    <i class="fas fa-${getIconForType(rec.type)}"></i>
                </div>
                <div class="rec-content">
                    <h4>${rec.title}</h4>
                    <p>${rec.description}</p>
                    <span class="rec-meta">${rec.duration} min • ${rec.difficulty}</span>
                </div>
                <a href="/course/${rec.id}" class="btn btn-primary btn-small">Start Learning</a>
            </div>
        `,
      )
      .join("");
  }
}

/**
 * Get Icon Based on Recommendation Type
 */
function getIconForType(type) {
  const icons = {
    video: "video",
    article: "book",
    quiz: "question-circle",
    exercise: "dumbbell",
    project: "code",
    default: "lightbulb",
  };

  return icons[type] || icons.default;
}

/**
 * Show Notification
 */
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.innerText = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add("show");
  }, 100);

  setTimeout(() => {
    notification.classList.remove("show");
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

/**
 * Show Achievement Notification
 */
function showAchievementNotification(achievement) {
  const achievementEl = document.createElement("div");
  achievementEl.className = "achievement-notification";
  achievementEl.innerHTML = `
        <div class="achievement-icon">
            <i class="fas fa-trophy"></i>
        </div>
        <div class="achievement-content">
            <h4>Achievement Unlocked!</h4>
            <p>${achievement}</p>
        </div>
    `;

  document.body.appendChild(achievementEl);

  setTimeout(() => {
    achievementEl.classList.add("show");
  }, 100);

  setTimeout(() => {
    achievementEl.remove();
  }, 5000);
}
