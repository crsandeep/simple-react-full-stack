const user = require('./jest.js');

// toEqual
test('User should be John Sangalang object', () => {
  expect(user.createUser()).toEqual({
    firstName: 'John',
    lastName: 'Sangalang',
  });
});
