/* eslint-disable no-undef */
const user = require('./jest.js').default;

// toEqual
test('User should be John Sangalang object', () => {
  expect(user.createUser()).toEqual({
    firstName: 'John',
    lastName: 'Sangalang',
  });
});
