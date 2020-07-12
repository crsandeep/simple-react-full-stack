import jwt from 'jsonwebtoken';
import moment from 'moment';

export function validateJwt(currentJwt) {
  if (currentJwt == null) {
    console.log('currentJwt missing');
    return false;
  }

  if (currentJwt.isAuthenticated == null || currentJwt.isAuthenticated === false) {
    console.log('isAuthenticated missing');
    return false;
  }

  if (currentJwt.userId == null || currentJwt.userId <= 0) {
    console.log('userId missing');
    return false;
  }

  if (currentJwt.token == null || currentJwt.token.length <= 0) {
    console.log('token missing');
    return false;
  }

  // check token inside
  const token = jwt.decode(currentJwt.token);

  if (currentJwt.userId !== token.userId) {
    console.log('userId not match');
    return false;
  }


  const expireTime = moment.unix(token.exp);

  if (expireTime.isBefore(new Date())) {
    console.log(`expire, ${expireTime}- ${new Date().getTime()}`);
    return false;
  }

  console.log('Valid user');
  return true; // valid token
}


export function handleExpire(history) {
  // history.push('/login');
}

export function validateUser(currentJwt, history) {
  const isValid = validateJwt(currentJwt);
  if (!isValid) {
    handleExpire(history);
  }
  return isValid;
}
