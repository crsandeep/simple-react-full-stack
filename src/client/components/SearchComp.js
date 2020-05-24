import React from 'react';
// eslint-disable-next-line import/no-duplicates
import { useRef } from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';
import {
  IconButton
} from '@material-ui/core/';
import {
  Row, Col, ButtonToolbar, Button
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ExpandLessIcon from '@material-ui/icons/ExpandLess';
import SearchIcon from '@material-ui/icons/Search';
import Switch from '@material-ui/core/Switch';
import ItemListComp from './ItemListComp';
import ItemCardComp from './ItemCardComp';
import BaseUIComp from './BaseUIComp';

const validateFormSchema = Yup.object().shape({
  keyword: Yup.string()
    .required('Keyword is required')
    .min(3, 'Keyword must be at least 3 characters')
    .trim(),
  colorCode: Yup.string()
    .min(1, 'Please select Card Color'),
  tags: Yup.string().nullable()
    .min(3, '#Tags must be at least 3 characters')
    .trim(),
  category: Yup.string()
    .min(1, 'Please select Category'),
  location: Yup.string()
    .min(1, 'Please select Location')
});

function SearchComp(props) {
  const formRef = useRef();

  const [isAdvanceMode, setAdvanceMode] = React.useState(false);

  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };
  const handleReset = () => {
    if (formRef.current) {
      formRef.current.handleReset();
    }
    setAdvanceMode(false);
  };

  // hook for switch view
  const [state, setState] = React.useState({
    isListView: false
  });
  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
  };

  return (
    <div>
      <BaseUIComp
        displayMsg={props.displayMsg}
        pageLoading={props.pageLoading}
      />

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
          <Formik
            enableReinitialize
            initialValues={props.formState}
            validationSchema={validateFormSchema}
            onSubmit={props.handleSearch}
            innerRef={formRef}
          >
            {({ values, errors, touched }) => (
              <Form>
                <Row>
                  <Col xs={6} md={8}>
                    <Field name="keyword" type="text" placeholder="Enter keyword" className={`form-control${errors.keyword && touched.keyword ? ' is-invalid' : ''}`} />
                    <ErrorMessage name="keyword" component="div" className="invalid-feedback" />
                  </Col>
                  <Col xs={6} md={4}>
                    <IconButton
                      aria-label="Search"
                      onClick={handleSubmit}
                    >
                      <SearchIcon />
                    </IconButton>
                    {isAdvanceMode === false
                       && (
                       <IconButton
                         aria-label="Show"
                         onClick={() => setAdvanceMode(true)}
                       >
                         <ExpandMoreIcon />
                       </IconButton>
                       )
                    }
                    {isAdvanceMode === true
                       && (
                       <IconButton
                         aria-label="Hide"
                         onClick={() => setAdvanceMode(false)}
                       >
                         <ExpandLessIcon />
                       </IconButton>
                       )
                    }

                    <IconButton
                      aria-label="Reset"
                      onClick={handleReset}
                    >
                      <HighlightOffIcon />
                    </IconButton>
                  </Col>
                </Row>
                {isAdvanceMode === true ? (
                  <Row>
                    <Col xs={6} md={6}>
                      <label htmlFor="category">Category</label>
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
                    <Col xs={6} md={6}>
                      <label htmlFor="tags">#Tags</label>
                      <Field name="tags" type="text" placeholder="" className={`form-control${errors.tags && touched.tags ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="tags" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                ) : null}

                {isAdvanceMode === true ? (
                  <Row>
                    <Col xs={6} md={6}>
                      <label htmlFor="location">Space Location</label>
                      <Field
                        name="location"
                        as="select"
                        placeholder="Location"
                        className={`form-control${
                          errors.location && touched.location
                            ? ' is-invalid'
                            : ''
                        }`}
                      >
                        <option value="">Please select...</option>
                        <option value="Living Room">Living Room</option>
                        <option value="Dinning Room">Dinning Room</option>
                        <option value="Kitechen">Kitechen</option>
                        <option value="Bathroom">Bathroom</option>
                        <option value="Bedroom 1">Bedroom 1</option>
                        <option value="Bedroom 2">Bedroom 2</option>
                        <option value="Bedroom 3">Bedroom 3</option>
                        <option value="Others">Others</option>
                      </Field>
                      <ErrorMessage
                        name="location"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={6} md={6}>
                      <label htmlFor="colorCode">Card Color</label>
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
                  </Row>
                ) : null}

              </Form>
            )}
          </Formik>
        </Col>
      </Row>
      <Row>
        <Col xs={12} md={12}>
          {
            !state.isListView ? (
              <ItemCardComp
                isShowLocation
                isReadOnly
                itemList={props.itemList}
              />
            ) : (
              <ItemListComp
                isShowLocation
                isReadOnly
                itemList={props.itemList}
              />
            )
          }
        </Col>
      </Row>
    </div>
  );
}

SearchComp.defaultProps = {
  itemList: []
};

SearchComp.propTypes = {
  itemList: PropTypes.arrayOf(PropTypes.object),
  pageLoading: PropTypes.bool.isRequired,
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  handleSearch: PropTypes.func.isRequired,
  handleGoBack: PropTypes.func.isRequired
};

export default SearchComp;
