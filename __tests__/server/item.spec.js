const request = require("supertest");
const express = require('express');
import { Container } from 'typedi';
    
//initial config
process.env.LOG_LEVEL = 'emerg';
process.env.MORGAN_LEVEL = 'tiny';

//initial app config
let itemId = null;
let expressApp = null;
beforeAll(async (done)=> {
  expressApp = await require('../../src/server/app');
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

describe('GET /item', () => {
  it('get by item Id', async () => {
    //invoke api
    const response = await request(expressApp).get('/api/item/4')

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

    //check 1st item
    const item = recBody.payload
    expect(item.spaceId).not.toBeNull();
    expect(item.itemId).not.toBeNull();
    expect(item.name).not.toBeNull();
    expect(item.category).not.toBeNull();
  });
});

describe('GET /item/space', () => {
  it('get by space Id', async () => {
    //invoke api
    const response = await request(expressApp).get('/api/item/space/1')

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

    //check 1st item
    const item = recBody.payload[0];
    expect(item.spaceId).not.toBeNull();
    expect(item.itemId).not.toBeNull();
    expect(item.name).not.toBeNull();
    expect(item.category).not.toBeNull();
  });
});


describe('POST /item', () => {
  it('missing mandatory input case', async () => {
    const submitValues = { };
    //prepare expect values
    const expectValues ={
      "isSuccess": false,
      "payload": null,
      "message": null
    };

    const defaultNumVal = 1;
    const defaultStr = "Test";
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
    expectValues.message = messageTemplate.replace('?',targetField);
    expect(recBody).toEqual(expectValues);

    //check other fields
    submitValues.spaceId = defaultNumVal;

    //missing name
    targetField = 'name';
    expectValues.message = messageTemplate.replace('?',targetField);
    response = await request(expressApp).post('/api/item').send(submitValues)
    expect(response.body).toEqual(expectValues);

    submitValues.name = defaultStr;
    
    //missing colorCode
    targetField = 'colorCode';
    expectValues.message = messageTemplate.replace('?',targetField);
    response = await request(expressApp).post('/api/item').send(submitValues)
    expect(response.body).toEqual(expectValues);

    submitValues.colorCode = defaultStr;


    //missing category
    targetField = 'category';
    expectValues.message = messageTemplate.replace('?',targetField);
    response = await request(expressApp).post('/api/item').send(submitValues)
    expect(response.body).toEqual(expectValues);

    submitValues.category = defaultStr;
  });

    
  it('positive case', async () => {
    const submitValues = {
      "itemId": null,
      "spaceId": 1,
      "name": "Item Name - 123",
      "tags": "business",
      "category": "clothes",
      "colorCode": "yellow",
      "description": "Item description - 123",
      "imgPath": null,
      "reminderDtm": "2020-03-27T03:17:09",
      "reminderComplete": null
    };

    //prepare expect values
    let expectValues = submitValues;
    delete expectValues.itemId;
    expectValues.reminderComplete = false;
    expectValues.reminderDtm = "2020-03-26T19:17:09.000Z"
      
    //invoke api
    const response = await request(expressApp).post('/api/item').send(submitValues)

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
    for (let [key, value] of Object.entries(expectValues)) {
      expect(recPayload[key]).toEqual(expectValues[key]);
    }

    //check specific
    //check item id is integer
    expect(Number.isNaN(recPayload.itemId)).toBe(false);

    //set itemid for further use
    itemId = recPayload.itemId;
  });
});