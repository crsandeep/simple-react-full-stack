const request = require('supertest');
const express = require('express');
const path = require('path');
import { Container } from 'typedi';

//initial config
process.env.LOG_LEVEL = 'emerg';
process.env.MORGAN_LEVEL = 'tiny';
const apiUrl = '/api/item';

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
const postImgFilePath = path.join(__dirname, 'test_image.jpg');
const updImgFilePath = path.join(__dirname, 'test_upd_image.jpg');
const imgDestPath = 'pload/images/item/';

function initalItemValues() {
  //post + get item values
  postItemValues = {
    spaceId: 1,
    name: 'Item Name - 123',
    tags: 'business',
    category: 'clothes',
    colorCode: 'yellow',
    description: 'Item description - 123',
    reminderDtm: '2020-03-27T01:17:09.000Z'
  };

  //update item values
  updItemValues = Object.assign({}, postItemValues);
  updItemValues.name = 'Item - ABCD';
  updItemValues.tags = 'casual';
  updItemValues.category = 'shoes';
  updItemValues.colorCode = 'red';
  updItemValues.description = 'Item content - ABC';
  updItemValues.reminderDtm = '2020-04-01T09:20:13.000Z'

  //expect post values
  expectPostResponse = {
    isSuccess: true,
    payload: {},  //to be copy from input
    message: null
  }
  expectPostResponse.payload =  Object.assign({}, postItemValues);
  // delete expectPostResponse.payload.itemId;
  expectPostResponse.payload.reminderComplete = false;
  expectPostResponse.payload.imgPath = null;

  //expect update values
  expectUpdResponse = {
    isSuccess: true,
    payload: {},  //to be copy from input
    message: null
  }
  expectUpdResponse.payload =  Object.assign({}, updItemValues);
  delete expectUpdResponse.payload.itemId;  //to be fill in during test
  expectUpdResponse.payload.reminderComplete = false;
  expectUpdResponse.payload.imgPath = null;

}

//loading app
beforeAll(async (done) => {
  expressApp = await require('../../src/server/app');
  
  //prepare item values
  initalItemValues();

  done();
});

//close the db connection
afterAll(async () => {
  const sequelize = Container.get('sequelize');
  // await sequelize.drop()
  await sequelize.close();
});

describe('Create Item without Image - POST /item', () => {
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
    response = await request(expressApp).post(apiUrl).send(submitValues)

    //start checking
    expect(response.statusCode).toEqual(500);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

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
    response = await request(expressApp).post(apiUrl).send(submitValues);
    expect(response.body).toEqual(expectValues);

    submitValues.name = defaultStr;

    //missing colorCode
    targetField = 'colorCode';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post(apiUrl).send(submitValues);
    expect(response.body).toEqual(expectValues);

    submitValues.colorCode = defaultStr;


    //missing category
    targetField = 'category';
    expectValues.message = messageTemplate.replace('?', targetField);
    response = await request(expressApp).post(apiUrl).send(submitValues);
    expect(response.body).toEqual(expectValues);

    submitValues.category = defaultStr;
  });


  it('positive case', async () => {

    //invoke api
    const response = await request(expressApp).post(apiUrl).send(postItemValues);

    //start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();


    const recPayload = response.body.payload;
    //check specific
    //check item id is integer
    expect(Number.isNaN(recPayload.itemId)).toBe(false);

    //set itemid for other test cases
    expectPostResponse.payload.itemId = recPayload.itemId;

    //check general attributes
    //compare all expect value attribute with submit value
    for (let [key, value] of Object.entries(expectPostResponse.payload)) {
      expect(recPayload[key]).toEqual(expectPostResponse.payload[key]);
    }

  });
});

describe('Get Item list - GET /item/space/:spaceId', () => {
  it('get by space Id', async () => {
    //invoke api
    const response = await request(expressApp).get(`${apiUrl}/space/${expectPostResponse.payload.spaceId}`);

    //start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

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


describe('Get Item - GET /item/:itemId', () => {
  it('get by item Id', async () => {
    //invoke api
    const response = await request(expressApp).get(`${apiUrl}/${expectPostResponse.payload.itemId}`);

    //start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

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

describe('Update Item with Image - PUT /item with file', () => {
  it('positive case', async () => {
    //copy item id
    updItemValues.itemId = expectPostResponse.payload.itemId;
    expectUpdResponse.payload.itemId = updItemValues.itemId;

    //prepare request
    let req = request(expressApp).put(`${apiUrl}/${updItemValues.itemId}`);
    for (let [key, value] of Object.entries(updItemValues)) {
      req.field(key, value);
    }
    req.attach('imgFile', updImgFilePath);

    //invoke api
    const response = await req;

    //start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    //check file path
    expect(recBody.payload.imgPath).toMatch(new RegExp('upload\/images\/item\/[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.jpg'));
    
    //set imgPath to null for below full comparsion
    recBody.payload.imgPath = null;

    //check value is exactly match 
    expect(recBody).toEqual(expectUpdResponse);

  });
});

describe('Delete Item - DELETE /item/:itemId', () => {
  it('positive case', async () => {
    //invoke api
    const response = await request(expressApp).delete(`${apiUrl}/${expectPostResponse.payload.itemId}`);

    //start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    recBody.payload.imgPath = null;
    
    //check value is exactly match 
    expect(recBody).toEqual(expectUpdResponse);
  });
  
});

describe('Create Item with Image - POST /item with file', () => {
  it('positive case', async () => {

    //prepare request
    let req = request(expressApp).post(apiUrl);
    for (let [key, value] of Object.entries(postItemValues)) {
      req.field(key, value);
    }
    req.attach('imgFile', postImgFilePath);

    //invoke api
    const response = await req;

    //start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    const recPayload = response.body.payload;
    //check file upload
    expect(recPayload.imgPath).toMatch(new RegExp('upload\/images\/item\/[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.jpg'));
    //set imgPath to null for below full comparsion
    recPayload.imgPath = null;
    
    //check specific
    //check item id is integer
    expect(Number.isNaN(recPayload.itemId)).toBe(false);

    //set itemid for other test cases
    expectPostResponse.payload.itemId = recPayload.itemId;

    //check general attributes
    //compare all expect value attribute with submit value
    for (let [key, value] of Object.entries(expectPostResponse.payload)) {
      expect(recPayload[key]).toEqual(expectPostResponse.payload[key]);
    }
  });
});

describe('Update Item without Image - PUT /item', () => {
  it('positive case', async () => {
    //copy item id
    updItemValues.itemId = expectPostResponse.payload.itemId;
    expectUpdResponse.payload.itemId = updItemValues.itemId;

    //invoke api
    const response = await request(expressApp).put(`${apiUrl}/${updItemValues.itemId}`).send(updItemValues);

    //start checking
    expect(response.statusCode).toEqual(201);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    //check existing image file remain exist even record is updated without new image provided
    expect(recBody.payload.imgPath).toMatch(new RegExp('upload\/images\/item\/[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.jpg'));
    //set imgPath to null for below full comparsion
    recBody.payload.imgPath = null;
    
    //check value is exactly match 
    expect(recBody).toEqual(expectUpdResponse);
  });
});


describe('Delete Item Image - DELETE /item/image/:itemId', () => {
  it('positive case', async () => {
    //invoke api
    const response = await request(expressApp).delete(`${apiUrl}/image/${expectPostResponse.payload.itemId}`);

    //start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).toBe(true);
  });
  
});


describe('Delete Item - DELETE /item/:itemId', () => {
  it('positive case', async () => {
    //invoke api
    const response = await request(expressApp).delete(`${apiUrl}/${expectPostResponse.payload.itemId}`);

    //start checking
    expect(response.statusCode).toEqual(200);

    const recBody = response.body;

    //check attributes
    expect(recBody).toHaveProperty('isSuccess');
    expect(recBody).toHaveProperty('message');
    expect(recBody).toHaveProperty('payload');

    //check values
    expect(recBody.isSuccess).toBe(true);
    expect(recBody.message).toBe(null);
    expect(recBody.payload).not.toBeNull();

    recBody.payload.imgPath = null;
    
    //check value is exactly match 
    expect(recBody).toEqual(expectUpdResponse);
  });
  
});