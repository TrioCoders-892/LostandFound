// Example: simple client-side form validation
document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const inputs = form.querySelectorAll("input, textarea, select");
      let valid = true;
      inputs.forEach((input) => {
        if (!input.value) valid = false;
      });
      if (!valid) {
        e.preventDefault();
        alert("Please fill all fields.");
      }
    });
  });
  const items = document.querySelectorAll(".item-card");
  items.forEach((item, index) => {
    item.style.animationDelay = `${index * 0.1}s`;
  });

  // ==================== MESSAGING SYSTEM JAVASCRIPT ====================

  // Auto-scroll to bottom of messages
  function scrollToBottom() {
    const messagesContainer = document.querySelector(".messages-container");
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Call scrollToBottom on conversation pages
  scrollToBottom();

  // Auto-resize textarea
  const textareas = document.querySelectorAll("textarea");
  textareas.forEach((textarea) => {
    textarea.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = this.scrollHeight + "px";
    });
  });

  // Message form validation
  const messageForms = document.querySelectorAll(
    'form[action*="send_message"]'
  );
  messageForms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      const messageTextarea = form.querySelector('textarea[name="message"]');
      if (messageTextarea && messageTextarea.value.trim().length === 0) {
        e.preventDefault();
        alert("Please enter a message.");
        messageTextarea.focus();
        return false;
      }
    });
  });

  // Add loading state to buttons
  const buttons = document.querySelectorAll('button[type="submit"]');
  buttons.forEach((button) => {
    button.addEventListener("click", function () {
      this.textContent = "Sending...";
      this.disabled = true;
    });
  });

  // Real-time message character count (optional)
  const messageTextarea = document.querySelector('textarea[name="message"]');
  if (messageTextarea) {
    const maxLength = 500;
    messageTextarea.setAttribute("maxlength", maxLength);

    // Create character count display
    const charCount = document.createElement("div");
    charCount.className = "char-count";
    charCount.style.fontSize = "12px";
    charCount.style.color = "#666";
    charCount.style.textAlign = "right";
    charCount.style.marginTop = "5px";
    messageTextarea.parentNode.insertBefore(
      charCount,
      messageTextarea.nextSibling
    );

    messageTextarea.addEventListener("input", function () {
      const remaining = maxLength - this.value.length;
      charCount.textContent = `${remaining} characters remaining`;
      if (remaining < 50) {
        charCount.style.color = "#dc3545";
      } else {
        charCount.style.color = "#666";
      }
    });

    // Trigger initial count
    messageTextarea.dispatchEvent(new Event("input"));
  }

  // Add smooth scrolling for better UX
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

  // Add confirmation for important actions
  const contactButtons = document.querySelectorAll(".btn-contact");
  contactButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      if (!confirm("Do you want to contact the owner/finder of this item?")) {
        e.preventDefault();
        return false;
      }
    });
  });

  // Add keyboard shortcuts
  document.addEventListener("keydown", function (e) {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const messageForm = document.querySelector(
        'form[action*="send_message"]'
      );
      if (messageForm && document.activeElement.tagName === "TEXTAREA") {
        messageForm.dispatchEvent(new Event("submit"));
      }
    }

    // Escape to go back
    if (e.key === "Escape") {
      const backButton = document.querySelector(".btn-secondary");
      if (backButton) {
        window.location.href = backButton.href;
      }
    }
  });

  // Add notification for unread messages (if on inbox page)
  const unreadBadges = document.querySelectorAll(".unread-badge");
  if (unreadBadges.length > 0) {
    // Simple notification (could be enhanced with browser notifications)
    console.log(`You have ${unreadBadges.length} unread message(s)`);
  }

  // Add loading animation for dynamic content
  const conversationCards = document.querySelectorAll(".conversation-card");
  conversationCards.forEach((card) => {
    card.addEventListener("click", function () {
      this.style.opacity = "0.7";
      setTimeout(() => {
        this.style.opacity = "1";
      }, 200);
    });
  });
});
