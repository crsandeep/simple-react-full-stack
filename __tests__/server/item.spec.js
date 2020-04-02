const request = require('supertest');
const express = require('express');
import { Container } from 'typedi';

//initial config
process.env.LOG_LEVEL = 'emerg';
process.env.MORGAN_LEVEL = 'tiny';

//initial app config
let expressApp = null;

//post + get
let postItemValues = null;
let expectPostResponse = null;

//upd
let updItemValues = null;
let expectUpdResponse = null;

//input and expect value setup
//update item details HERE
function initalItemValues() {
  //post + get item values
  postItemValues = {
    itemId: null,
    spaceId: 1,
    name: 'Item Name - 123',
    tags: 'business',
    category: 'clothes',
    colorCode: 'yellow',
    description: 'Item description - 123',
    imgPath: null,
    reminderDtm: '2020-03-27T03:17:09',
    reminderComplete: null
  };

  //update item values
  updItemValues = postItemValues;
  updItemValues.name = 'Item - ABCD';
  updItemValues.tags = 'casual';
  updItemValues.category = 'shoes';
  updItemValues.colorCode = 'red';
  updItemValues.description = 'Item content - ABC';
  updItemValues.reminderDtm = '2020-04-01T03:17:09'

  //expect post values
  expectPostResponse = {
    isSuccess: true,
    payload: {},  //to be copy from input
    message: null
  }
  expectPostResponse.payload = postItemValues;
  delete expectPostResponse.payload.itemId;
  expectPostResponse.payload.reminderComplete = false;
  expectPostResponse.payload.reminderDtm = '2020-03-27T19:17:09.000Z';


  //expect update values
  expectUpdResponse = {
    isSuccess: true,
    payload: {},  //to be copy from input
    message: null
  }
  expectUpdResponse.payload = updItemValues;
  delete expectUpdResponse.payload.itemId;  //to be fill in during test
  expectUpdResponse.payload.reminderComplete = false;
  expectUpdResponse.payload.reminderDtm = '2020-04-01T19:17:09.000Z';

}

beforeAll(async (done) => {
  expressApp = await require('../../src/server/app');

  //prepare item values
  initalItemValues();

  done();
});

afterAll(async () => {
  const conn = Container.get('mongooseConn');
  // const itemModel = Container.get('itemModel');
  // await itemModel.counterReset('itemId', function(err) {
  //   console.log(`The counter was reset ${err}`)
  // Now the counter is 0
  // });
  // itemModel._resetCount().then(val => console.log(`The counter was reset to ${val}`));
  await conn.close();
});

describe('POST /item', () => {
  it('missing mandatory input case', async () => {
    const submitValues = {};
    //prepare expect values
    const expectValues = {
      isSuccess: false,
      payload: null,
      message: null
    };

    const defaultNumVal = 1;
    const defaultStr = 'Test';
    const messageTemplate = "\"?\" is required";
    let response;
    let targetField;

    //invoke api
    response = await request(expressApp).post('/api/item').send(submitValues)

    //start checking
    expect(response.statusCode).toEqual(500)

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess')
    expect(recBody).toHaveProperty('message')
    expect(recBody).toHaveProperty('payload')

    //check values
    expect(recBody.isSuccess).toBe(false);
    expect(recBody.payload).toBe(null);
    expect(recBody.message).not.toBeNull();

    //check 1st detect mandatory
    //missing spaceId
    targetField = 'spaceId';
    expectValues.message = messageTemplate.replace('?', targetField);
    expect(recBody).toEqual(expectValues);

    //check other fields
    submitValues.spaceId = defaultNumVal;

    //missing name
    targetField = 'name';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post('/api/item').send(submitValues)
    expect(response.body).toEqual(expectValues);

    submitValues.name = defaultStr;

    //missing colorCode
    targetField = 'colorCode';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post('/api/item').send(submitValues)
    expect(response.body).toEqual(expectValues);

    submitValues.colorCode = defaultStr;


    //missing category
    targetField = 'category';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post('/api/item').send(submitValues)
    expect(response.body).toEqual(expectValues);

    submitValues.category = defaultStr;
  });


  it('positive case', async () => {

    //invoke api
    const response = await request(expressApp).post('/api/item').send(postItemValues)

    //start checking
    expect(response.statusCode).toEqual(201)

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess')
    expect(recBody).toHaveProperty('message')
    expect(recBody).toHaveProperty('payload')

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    //check general attributes
    //compare all expect value attribute with submit value
    const recPayload = response.body.payload;
    for (let [key, value] of Object.entries(expectPostResponse.payload)) {
      expect(recPayload[key]).toEqual(expectPostResponse.payload[key]);
    }

    //check specific
    //check item id is integer
    expect(Number.isNaN(recPayload.itemId)).toBe(false);

    //set itemid for other test cases
    expectPostResponse.payload.itemId = recPayload.itemId;
  });
});

describe('GET /item/space', () => {
  it('get by space Id', async () => {
    //invoke api
    const response = await request(expressApp).get(`/api/item/space/${expectPostResponse.payload.spaceId}`)

    //start checking
    expect(response.statusCode).toEqual(200)

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess')
    expect(recBody).toHaveProperty('message')
    expect(recBody).toHaveProperty('payload')

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    //check at least 1 item exists
    expect(recBody.payload.length).toBeGreaterThanOrEqual(0);

    //check 1st item
    const item = recBody.payload[0];
    expect(item.spaceId).not.toBeNull();
    expect(item.itemId).not.toBeNull();
    expect(item.name).not.toBeNull();
    expect(item.category).not.toBeNull();
  });
});


describe('GET /item', () => {
  it('get by item Id', async () => {
    //invoke api
    const response = await request(expressApp).get(`/api/item/${expectPostResponse.payload.itemId}`)

    //start checking
    expect(response.statusCode).toEqual(200)

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess')
    expect(recBody).toHaveProperty('message')
    expect(recBody).toHaveProperty('payload')

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    //check item attribute not null
    const item = recBody.payload
    expect(item.spaceId).not.toBeNull();
    expect(item.itemId).not.toBeNull();
    expect(item.name).not.toBeNull();
    expect(item.category).not.toBeNull();

    //check value is exactly match with post values
    expect(recBody).toEqual(expectPostResponse);
  });
});

describe('PUT /item', () => {
  it('positive case', async () => {
    //copy item id
    updItemValues.itemId = expectPostResponse.payload.itemId;

    //invoke api
    const response = await request(expressApp).put(`/api/item/${updItemValues.itemId}`).send(updItemValues)

    //start checking
    expect(response.statusCode).toEqual(201)

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess')
    expect(recBody).toHaveProperty('message')
    expect(recBody).toHaveProperty('payload')

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    //check value is exactly match 
    expect(recBody).toEqual(expectUpdResponse);
  });
});

