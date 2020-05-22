import React from 'react';
// eslint-disable-next-line import/no-duplicates
import { useRef } from 'react';

import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';
import {
  ListItemSecondaryAction,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  IconButton,
  ListItemAvatar,
  Avatar,
  Typography
} from '@material-ui/core/';
import {
  Button, Modal, Row, Col, Card, ButtonToolbar, CardColumns,
  Spinner, Image, Badge, Alert
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import AddAlertIcon from '@material-ui/icons/AddAlert';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import CardGiftcardIcon from '@material-ui/icons/CardGiftcard';
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import RefreshIcon from '@material-ui/icons/Refresh';
import MenuBookIcon from '@material-ui/icons/MenuBook';
import BuildIcon from '@material-ui/icons/Build';
import EmojiEventsIcon from '@material-ui/icons/EmojiEvents';
import FavoriteBorderIcon from '@material-ui/icons/FavoriteBorder';
import FlightIcon from '@material-ui/icons/Flight';
import RestaurantIcon from '@material-ui/icons/Restaurant';
import KitchenIcon from '@material-ui/icons/Kitchen';
import HelpOutlineIcon from '@material-ui/icons/HelpOutline';
import ChildFriendlyIcon from '@material-ui/icons/ChildFriendly';

import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';

import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import Link from '@material-ui/core/Link';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import * as Constants from '../constants/Item';
import RemindNoteComp from './RemindNoteComp';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  colorCode: Yup.string()
    .required('Color is required')
    .min(1, 'Please select Card Color'),
  description: Yup.string().nullable()
    .min(3, 'Description must be at least 3 characters')
    .trim(),
  tags: Yup.string().nullable()
    .min(3, '#Tags must be at least 3 characters')
    .trim(),
  category: Yup.string()
    .required('Category is required')
    .min(1, 'Please select Category')
});

// generate item content in list view

const genListData = (itemList, handleEdit, handleDelete) => {
  const elementList = [];

  for (const item of itemList) {
    let tagsArr = [];
    if (item.tags != null && item.tags.length > 0) {
      tagsArr = item.tags.split(',');
    }

    elementList.push(
      <ListItem
        key={item.itemId}
        alignItems="flex-start"
        button
      >
        <ListItemAvatar>
          {item.imgPath != null ? (
            <Avatar variant="rounded" alt={item.name} src={item.imgPath} />
          ) : (
            <Avatar variant="rounded" alt={item.name}>
              {
                item.name.substring(0, 4)
              }
            </Avatar>
          )}
        </ListItemAvatar>
        <ListItemText
          primary={item.name}
          secondary={(
            <React.Fragment>
              <Typography
                component="span"
                variant="body2"
                className="spaceList-inline"
                color="textSecondary"
              >
                {item.description}
                {
                  item.description != null && tagsArr != null && tagsArr.length > 0
                    ? (<br />) : null
                }
                {
                  tagsArr.map(tag => (
                    <Badge key={tag} variant="warning">
                      {tag}
                    </Badge>
                  ))
                }
              </Typography>
              {
                item.description != null || (tagsArr != null && tagsArr.length > 0)
                  ? (<br />) : null
              }
              {/* //reminder */}
              <RemindNoteComp remindDtm={item.reminderDtm} />
              {
                item.reminderDtm != null
                  ? (<br />) : null
              }

              {/* // ignore breadcrumbs as it triger ol cannot appear as a descendant of p tag issue */}
              <Link color="inherit" href="/space">
                <i className="fa fa-fw fa-home" style={{ fontSize: '1.05em' }} />
                {
                    // show space name
                    `${item.spaceLocation} - ${item.spaceName}`
                  }
              </Link>
              {' > '}
              <Link color="inherit" href="/grid">
                <i className="fa fa-fw fa-table" style={{ fontSize: '1.05em' }} />
                {
                    // show location with grid ID with 2 digits
                    item.gridId.toString().padStart(2, '0').slice(-3)
                  }
              </Link>
            </React.Fragment>
          )}
        />
        <ListItemSecondaryAction>
          <IconButton aria-label="edit" onClick={() => handleEdit(item.itemId)}>
            <EditIcon />
          </IconButton>
          <IconButton aria-label="delete" onClick={() => handleDelete(item.itemId, item.name, item.description)}>
            <DeleteIcon />
          </IconButton>
        </ListItemSecondaryAction>
      </ListItem>
    );
  }
  return elementList;
};


const genListView = (itemList, handleEdit, handleDelete) => {
  const displayList = [];
  const itemMap = new Map();
  let tempList = null;

  // prepare Map<category,List<Item>> for further generation
  for (const item of itemList) {
    // get corresponding list
    if (itemMap.get(item.category) != null) {
      tempList = itemMap.get(item.category);
    } else {
      tempList = [];
    }

    // add to list
    tempList.push(item);

    // update map with latest list
    itemMap.set(item.category, tempList);
  }

  // generate header and related spaces under each location according to Map settings
  for (const [category, list] of itemMap) {
    displayList.push(
      <li key={`section-${category}`}>
        <ul className="spaceList-ul">
          <ListSubheader>
            {
              {
                Favorite: <FavoriteBorderIcon />,
                Travel: <FlightIcon />,
                Clothes: <i className="fas fa-tshirt" />,
                Shoes: <i className="fas fa-shoe-prints" />,
                Collections: <EmojiEventsIcon />,
                Baby: <ChildFriendlyIcon />,
                Books: <MenuBookIcon />,
                Gifts: <CardGiftcardIcon />,
                Food: <RestaurantIcon />,
                Kitchenware: <KitchenIcon />,
                Tools: <BuildIcon />,
                Others: <HelpOutlineIcon />
              }[category]
            }
            {' '}
            {category}
          </ListSubheader>
          {genListData(list, handleEdit, handleDelete)}
        </ul>
      </li>
    );
  }
  return displayList;
};

// generate item content in card view
const genCardData = (itemList, handleEdit, handleDelete) => {
  const displayList = [];

  for (const item of itemList) {
    let tagsArr = [];
    if (item.tags != null && item.tags.length > 0) {
      tagsArr = item.tags.split(',');
    }

    displayList.push(
      <Card key={item.itemId} bg={item.colorCode.toLowerCase()}>
        {
          item.imgPath != null
            && <Card.Img variant="top" src={item.imgPath} />
        }
        <Card.Header>
          {item.name}
          <Badge className="float-right" variant="light">
            {
              {
                Favorite: <FavoriteBorderIcon />,
                Travel: <FlightIcon />,
                Clothes: <i className="fas fa-tshirt" />,
                Shoes: <i className="fas fa-shoe-prints" />,
                Collections: <EmojiEventsIcon />,
                Baby: <ChildFriendlyIcon />,
                Books: <MenuBookIcon />,
                Gifts: <CardGiftcardIcon />,
                Food: <RestaurantIcon />,
                Kitchenware: <KitchenIcon />,
                Tools: <BuildIcon />,
                Others: <HelpOutlineIcon />
              }[item.category]
            }
            {' '}
            {' '}
            {item.category}
          </Badge>
        </Card.Header>

        {/* //card content, description + tags */}
        {
          item.description != null
            || (tagsArr != null && tagsArr.length > 0) ? (
              <Card.Body>
                {/* //description row */}
                {
                  item.description != null ? (
                    <Row>
                      <Col xs={12} md={12}>
                        <Card.Text>item.description </Card.Text>
                      </Col>
                    </Row>
                  )
                    : null
                }

                {/* //tags row */}
                {
                  tagsArr != null && tagsArr.length > 0
                  && (
                  <Row>
                    <Col xs={12} md={12}>
                      {
                            tagsArr.map((tags, i) => (
                              <span key={i}>
                                <Badge variant="warning">
                                  #
                                  {tags}
                                </Badge>
                                {' '}
                              </span>
                            ))
                          }
                    </Col>
                  </Row>
                  )
                }
              </Card.Body>
            ) : null
        }

        <Card.Footer>
          {/* //reminder + button */}
          <Row>
            <Col xs={12} md={12}>
              {/* //Reminder */}
              <div>
                <RemindNoteComp remindDtm={item.reminderDtm} />

                <span style={{ float: 'right' }}>
                  <IconButton aria-label="edit" onClick={() => handleEdit(item.itemId)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton aria-label="delete" onClick={() => handleDelete(item.itemId, item.name, item.description)}>
                    <DeleteIcon />
                  </IconButton>
                </span>
              </div>
            </Col>
          </Row>

          {/* //location path */}
          <Row>
            <Col xs={12} md={12}>
              <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
                <Link color="inherit" href="/space">
                  <i className="fa fa-fw fa-home" style={{ fontSize: '1.05em' }} />
                  {
                    // show space name
                    `${item.spaceLocation} - ${item.spaceName}`
                  }
                </Link>
                <Link color="inherit" href="/grid">
                  <i className="fa fa-fw fa-table" style={{ fontSize: '1.05em' }} />
                  {
                    // show location with grid ID with 2 digits
                    item.gridId.toString().padStart(2, '0').slice(-3)
                  }
                </Link>
              </Breadcrumbs>
            </Col>
          </Row>
        </Card.Footer>
      </Card>
    );
  }
  return displayList;
};

function ItemComp(props) {
  const formRef = useRef();
  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };


  // hook for switch view
  const [state, setState] = React.useState({
    isListView: false
  });
  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
  };


  // generate item data
  let dataList = [];
  if (props.itemList != null && props.itemList.length > 0) {
    if (!state.isListView) {
      // card view
      dataList = genCardData(props.itemList, props.handleEdit, props.handleDelete);
    } else {
      // list view
      dataList = genListView(props.itemList, props.handleEdit, props.handleDelete);
    }
  }

  return (
    <div>
      {
        props.displayMsg.isSuccess !== null ? (
          props.displayMsg.isSuccess === true ? (
            <Alert variant="success">
              {props.displayMsg.msg}
            </Alert>
          )
            : (
              <Alert variant="danger">
                {props.displayMsg.msg}
              </Alert>
            )
        ) : null
      }

      {
        // page loading mask
        props.formState.pageLoading === true
          && (
          <div className="overlay">
            <Spinner
              animation="border"
              role="status"
              size="lg"
              style={{ width: `${10}rem`, height: `${10}rem` }}
              className="mt-5"
            >
              <span className="sr-only">Loading...</span>
            </Spinner>
            <h5>Loading...</h5>
          </div>
          )
      }

      <Row>
        <Col xs={2} md={1}>
          <IconButton
            aria-label="back"
            onClick={() => props.handleGoBack()}
          >
            <ArrowBackIosIcon />
          </IconButton>
        </Col>
        <Col xs={10} md={11}>
          <ButtonToolbar>
            {
                // new item button
                props.formState.formMode === Constants.FORM_READONLY_MODE
                  && (
                  <IconButton aria-label="New" onClick={props.handleNew}>
                    <AddCircleOutlineIcon />
                  </IconButton>
                  )
              }

            <IconButton aria-label="Cancel" onClick={props.handleReloadList}>
              <RefreshIcon />
            </IconButton>

            <FormControlLabel
              control={(
                <Switch
                  checked={state.isListView}
                  onChange={handleChange}
                  name="isListView"
                  color="primary"
                />
              )}
              label="List View"
            />
          </ButtonToolbar>
        </Col>
      </Row>
      <Row>
        <Col xs={12} md={12}>

          {
            !state.isListView ? (
              <CardColumns>
                {dataList}
              </CardColumns>
            ) : (
              <List className="spaceList-pc" subheader={<li />}>
                {dataList}
              </List>
            )
          }
        </Col>
      </Row>

      <div>
        <Modal
          show={props.formState.formMode === Constants.FORM_EDIT_MODE}
          onHide={props.handleCancel}
        >
          <Modal.Header closeButton>
            <Modal.Title>Item Details</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Formik
              enableReinitialize
              initialValues={props.formState}
              validationSchema={validateFormSchema}
              onSubmit={props.handleFormSave}
              innerRef={formRef}
            >
              {({ values, errors, touched }) => (
                <Form>
                  <Row className="justify-content-md-center">
                    <Col xs={12} md={8}>
                      <Field name="imgPath">
                        {({ field, form, meta }) => (
                          field.value != null
                            && (
                            <div>
                              <Image src={field.value} fluid />
                              {
                                form.values.imgPath != null
                                && (
                                <IconButton
                                  aria-label="delete"
                                  className="align-bottom"
                                  onClick={() => props.handleRemoveItemImg(form.values.itemId)
                                  }
                                >
                                  <DeleteIcon />
                                </IconButton>
                                )
                              }
                            </div>
                            )
                        )}
                      </Field>
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={12}>
                      <label htmlFor="name" className="required-field">Name</label>
                      <Field name="name" type="text" placeholder="Your Item Name" className={`form-control${errors.name && touched.name ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="name" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={6}>
                      <label htmlFor="category" className="required-field">Category</label>
                      <Field name="category" as="select" placeholder="Category" className={`form-control${errors.category && touched.category ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Favorite">Favorite</option>
                        <option value="Gifts">Gifts</option>
                        <option value="Clothes">Clothes</option>
                        <option value="Shoes">Shoes</option>
                        <option value="Collections">Collections</option>
                        <option value="Baby">Baby</option>
                        <option value="Books">Books</option>
                        <option value="Travel">Travel</option>
                        <option value="Food">Food</option>
                        <option value="Kitchenware">Kitchenware</option>
                        <option value="Tools">Tools</option>
                        <option value="Others">Others</option>
                      </Field>
                      <ErrorMessage name="category" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={12} md={6}>
                      <label htmlFor="tags">#Tags</label>
                      <Field name="tags" type="text" placeholder="Use commas to separate" className={`form-control${errors.tags && touched.tags ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="tags" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={6}>
                      <label htmlFor="colorCode" className="required-field">Card Color</label>
                      <Field name="colorCode" as="select" placeholder="Color" className={`form-control${errors.colorCode && touched.colorCode ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Light" default>Light</option>
                        <option value="Primary">Blue</option>
                        <option value="Secondary">Grey</option>
                        <option value="Success">Green</option>
                        <option value="Danger">Red</option>
                        <option value="Info">Cyan</option>
                      </Field>
                      <ErrorMessage name="colorCode" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={12} md={6}>
                      <label htmlFor="imgFile">Photo</label>
                      <Field name="imgFile">
                        {({ field, form, meta }) => (
                          <input
                            type="file"
                            onChange={event => form.setFieldValue('imgFile', event.target.files[0])
                              }
                            accept="image/*"
                            className={`form-control${errors.imgFile && touched.imgFile ? ' is-invalid' : ''}`}
                          />
                        )}
                      </Field>
                      <ErrorMessage name="imgFile" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={12}>
                      <label htmlFor="description">Description</label>
                      <Field
                        name="description"
                        component="textarea"
                        placeholder="E.g. 2nd Wedding Anniversary gift from your wife. "
                        className={`form-control${errors.description && touched.description ? ' is-invalid' : ''}`}
                      />
                      <ErrorMessage name="description" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={6}>
                      <label htmlFor="reminderDtm">Reminder</label>
                      <AddAlertIcon />
                      <Field name="reminderDtm">
                        {({ field, form, meta }) => (
                          <DatePicker
                            onChange={date => form.setFieldValue('reminderDtm', date)
                              }
                            selected={values.reminderDtm}
                            dateFormat="dd-MMM-yyyy hh:mm aa"
                            placeholder="Reminder"
                            todayButton="Today"
                            showTimeSelect
                            timeIntervals={15}
                            className={`datepicker-200w form-control${errors.reminderDtm && touched.reminderDtm ? ' is-invalid' : ''}`}
                          />
                        )}
                      </Field>
                      <ErrorMessage name="reminderDtm" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                </Form>
              )}
            </Formik>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={props.handleCancel}>Close</Button>
            <Button id="btnSave" variant="primary" onClick={handleSubmit}>Save changes</Button>
          </Modal.Footer>
        </Modal>
      </div>
    </div>
  );
}

ItemComp.defaultProps = {
  itemList: []
};

ItemComp.propTypes = {
  itemList: PropTypes.arrayOf(PropTypes.object),
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  handleFormSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleNew: PropTypes.func.isRequired,
  handleEdit: PropTypes.func.isRequired,
  handleDelete: PropTypes.func.isRequired,
  handleReloadList: PropTypes.func.isRequired,
  handleRemoveItemImg: PropTypes.func.isRequired,
  handleGoBack: PropTypes.func.isRequired
};

export default ItemComp;
