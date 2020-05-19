/* eslint-disable import/no-unresolved */
/* eslint-disable no-undef */
import { Container } from 'typedi';

const request = require('supertest');
const path = require('path');

// initial config
process.env.LOG_LEVEL = 'emerg';
process.env.MORGAN_LEVEL = 'tiny';
const apiUrl = '/api/space';

// initial app config
let expressApp = null;

// post + get
let postSpaceValues = null;
let expectPostResponse = null;

// upd
let updSpaceValues = null;
let expectUpdResponse = null;

// input and expect value setup
// update space details HERE
const postImgFilePath = path.join(__dirname, 'test_image.jpg');
const updImgFilePath = path.join(__dirname, 'test_upd_image.jpg');

function initalSpaceValues() {
  // post + get space values
  postSpaceValues = {
    userId: 1,
    name: 'Space Name - 123',
    tags: 'business',
    location: 'Bedroom 1'
  };

  // update space values
  updSpaceValues = Object.assign({}, postSpaceValues);
  updSpaceValues.name = 'Space - ABCD';
  updSpaceValues.tags = 'casual';
  updSpaceValues.location = 'Living Room';

  // expect post values
  expectPostResponse = {
    isSuccess: true,
    payload: {}, // to be copy from input
    message: null
  };
  expectPostResponse.payload = Object.assign({}, postSpaceValues);
  // delete expectPostResponse.payload.spaceId;
  expectPostResponse.payload.imgPath = null;

  // expect update values
  expectUpdResponse = {
    isSuccess: true,
    payload: {}, // to be copy from input
    message: null
  };
  expectUpdResponse.payload = Object.assign({}, updSpaceValues);
  delete expectUpdResponse.payload.spaceId; // to be fill in during test
  expectUpdResponse.payload.imgPath = null;
}

// loading app
beforeAll(async (done) => {
  expressApp = await require('../../src/server/app');

  // prepare space values
  initalSpaceValues();

  done();
});

// close the db connection
afterAll(async () => {
  const sequelize = Container.get('sequelize');
  // await sequelize.drop()
  await sequelize.close();
});

describe('Create Space without Image - POST /space', () => {
  it('missing mandatory input case', async () => {
    const submitValues = {};
    // prepare expect values
    const expectValues = {
      isSuccess: false,
      payload: null,
      message: null
    };

    const defaultNumVal = 1;
    const defaultStr = 'Test';
    const messageTemplate = '"?" is required';
    let response;
    let targetField;

    // invoke api
    response = await request(expressApp).post(apiUrl).send(submitValues);

    // start checking
    expect(response.statusCode).toEqual(500);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(false);
    expect(recBody.payload).toBe(null);
    expect(recBody.message).not.toBeNull();

    // check 1st detect mandatory
    // missing userId
    targetField = 'userId';
    expectValues.message = messageTemplate.replace('?', targetField);
    expect(recBody).toEqual(expectValues);

    // check other fields
    submitValues.userId = defaultNumVal;

    // missing name
    targetField = 'name';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post(apiUrl).send(submitValues);
    expect(response.body).toEqual(expectValues);

    submitValues.name = defaultStr;

    // missing location
    targetField = 'location';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post(apiUrl).send(submitValues);
    expect(response.body).toEqual(expectValues);

    submitValues.location = defaultStr;
  });


  it('positive case', async () => {
    // invoke api
    const response = await request(expressApp).post(apiUrl).send(postSpaceValues);

    // start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();


    const recPayload = response.body.payload;
    // check specific
    // check space id is integer
    expect(Number.isNaN(recPayload.spaceId)).toBe(false);

    // set spaceid for other test cases
    expectPostResponse.payload.spaceId = recPayload.spaceId;

    // check general attributes
    // compare all expect value attribute with submit value
    for (const [key, value] of Object.entries(expectPostResponse.payload)) {
      expect(recPayload[key]).toEqual(expectPostResponse.payload[key]);
    }
  });
});

describe('Get Space list - GET /space/user/:userId', () => {
  it('get by user Id', async () => {
    // invoke api
    const response = await request(expressApp).get(`${apiUrl}/user/${expectPostResponse.payload.userId}`);

    // start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    // check at least 1 space exists
    expect(recBody.payload.length).toBeGreaterThanOrEqual(0);

    // check 1st space
    const space = recBody.payload[0];
    expect(space.userId).not.toBeNull();
    expect(space.spaceId).not.toBeNull();
    expect(space.name).not.toBeNull();
    expect(space.location).not.toBeNull();
  });
});


describe('Get Space - GET /space/:spaceId', () => {
  it('get by space Id', async () => {
    // invoke api
    const response = await request(expressApp).get(`${apiUrl}/${expectPostResponse.payload.spaceId}`);

    // start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    // check space attribute not null
    const space = recBody.payload;
    expect(space.userId).not.toBeNull();
    expect(space.spaceId).not.toBeNull();
    expect(space.name).not.toBeNull();
    expect(space.location).not.toBeNull();

    // check value is exactly match with post values
    expect(recBody).toEqual(expectPostResponse);
  });
});

describe('Update Space with Image - PUT /space with file', () => {
  it('positive case', async () => {
    // copy space id
    updSpaceValues.spaceId = expectPostResponse.payload.spaceId;
    expectUpdResponse.payload.spaceId = updSpaceValues.spaceId;

    // prepare request
    const req = request(expressApp).put(`${apiUrl}/${updSpaceValues.spaceId}`);
    for (const [key, value] of Object.entries(updSpaceValues)) {
      req.field(key, value);
    }
    req.attach('imgFile', updImgFilePath);

    // invoke api
    const response = await req;

    // start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    // check file path
    expect(recBody.payload.imgPath).toMatch(new RegExp('upload\/images\/space\/[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.jpg'));

    // set imgPath to null for below full comparsion
    recBody.payload.imgPath = null;

    // check value is exactly match
    expect(recBody).toEqual(expectUpdResponse);
  });
});

describe('Delete Space - DELETE /space/:spaceId', () => {
  it('positive case', async () => {
    // invoke api
    const response = await request(expressApp).delete(`${apiUrl}/${expectPostResponse.payload.spaceId}`);

    // start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    recBody.payload.imgPath = null;

    // check value is exactly match
    expect(recBody).toEqual(expectUpdResponse);
  });
});

describe('Create Space with Image - POST /space with file', () => {
  it('positive case', async () => {
    // prepare request
    const req = request(expressApp).post(apiUrl);
    for (const [key, value] of Object.entries(postSpaceValues)) {
      req.field(key, value);
    }
    req.attach('imgFile', postImgFilePath);

    // invoke api
    const response = await req;

    // start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    const recPayload = response.body.payload;
    // check file upload
    expect(recPayload.imgPath).toMatch(new RegExp('upload\/images\/space\/[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.jpg'));
    // set imgPath to null for below full comparsion
    recPayload.imgPath = null;

    // check specific
    // check space id is integer
    expect(Number.isNaN(recPayload.spaceId)).toBe(false);

    // set spaceid for other test cases
    expectPostResponse.payload.spaceId = recPayload.spaceId;

    // check general attributes
    // compare all expect value attribute with submit value
    for (const [key, value] of Object.entries(expectPostResponse.payload)) {
      expect(recPayload[key]).toEqual(expectPostResponse.payload[key]);
    }
  });
});

describe('Update Space without Image - PUT /space', () => {
  it('positive case', async () => {
    // copy space id
    updSpaceValues.spaceId = expectPostResponse.payload.spaceId;
    expectUpdResponse.payload.spaceId = updSpaceValues.spaceId;

    // invoke api
    const response = await request(expressApp).put(`${apiUrl}/${updSpaceValues.spaceId}`).send(updSpaceValues);

    // start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    // check existing image file remain exist even record is updated without new image provided
    expect(recBody.payload.imgPath).toMatch(new RegExp('upload\/images\/space\/[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.jpg'));
    // set imgPath to null for below full comparsion
    recBody.payload.imgPath = null;

    // check value is exactly match
    expect(recBody).toEqual(expectUpdResponse);
  });
});


describe('Delete Space Image - DELETE /space/image/:spaceId', () => {
  it('positive case', async () => {
    // invoke api
    const response = await request(expressApp).delete(`${apiUrl}/image/${expectPostResponse.payload.spaceId}`);

    // start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).toBe(true);
  });
});


describe('Delete Space - DELETE /space/:spaceId', () => {
  it('positive case', async () => {
    // invoke api
    const response = await request(expressApp).delete(`${apiUrl}/${expectPostResponse.payload.spaceId}`);

    // start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    // check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    // check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    recBody.payload.imgPath = null;

    // check value is exactly match
    expect(recBody).toEqual(expectUpdResponse);
  });
});
