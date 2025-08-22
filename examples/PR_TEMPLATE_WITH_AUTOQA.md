# Pull Request Template with AutoQA

## Description
Brief description of the changes in this PR.

## Changes Made
- [ ] List your changes here
- [ ] Add checkboxes as needed

## AutoQA Test Cases

Use the format below to automatically generate tests for your changes:

### Example: User Authentication Flow
AutoQA:user-login
1. Navigate to login page at "/login"
2. Enter email "test@example.com" in email field
3. Enter password "testpassword" in password field
4. Click the "Login" button
5. Verify user is redirected to dashboard page
6. Verify welcome message "Welcome back!" is displayed

### Example: Form Validation
AutoQA:form-validation
1. Navigate to contact form at "/contact"
2. Click submit button without filling any fields
3. Verify error message "Email is required" appears
4. Enter invalid email "notanemail"
5. Verify error message "Please enter a valid email" appears
6. Enter valid email "user@example.com"
7. Verify error message disappears

### Example: Shopping Cart Functionality
AutoQA:shopping-cart
1. Navigate to products page at "/products"
2. Click "Add to Cart" button on first product
3. Verify cart badge shows count of "1"
4. Click cart icon to open cart modal
5. Verify product appears in cart with correct name and price
6. Click "Remove" button for the product
7. Verify cart is empty and shows "Your cart is empty"

## AutoQA Guidelines

### Naming Convention
- Use descriptive scenario names: `AutoQA:feature-action`
- Examples: `AutoQA:user-registration`, `AutoQA:payment-flow`, `AutoQA:search-functionality`

### Writing Good Test Steps
1. **Be specific**: Use exact text and selectors when possible
2. **Include URLs**: Specify page paths like "/login", "/dashboard"
3. **Use quotes**: Wrap text content in quotes "Login", "Welcome!"
4. **Verify outcomes**: Include verification steps for important actions
5. **Number steps**: Keep steps sequential and logical

### React-Specific Tips
- Use data-testid attributes in your components
- Reference components by their test IDs
- Include state changes and React Router navigation
- Test both desktop and mobile viewports when relevant

## Testing Checklist
- [ ] AutoQA tags are properly formatted
- [ ] Test steps are clear and specific
- [ ] Staging environment is accessible
- [ ] Components have appropriate test IDs

---

**Note**: Tests will be automatically generated and executed against the staging environment when this PR is created or updated.